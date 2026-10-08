from __future__ import annotations

import os
import logging
import secrets
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from aplicacion.base_datos import Database
from aplicacion.rutas import router
from aplicacion.servicios import DomainError

logger = logging.getLogger(__name__)


def create_app(database_url: str | None = None, auth_secret: str | bytes | None = None) -> FastAPI:
    database = Database(database_url)
    configured_secret = auth_secret or os.getenv("QR_PASS_AUTH_SECRET")
    is_production = os.getenv("QR_PASS_ENV", "").lower() == "production"
    if configured_secret is None:
        if is_production:
            raise RuntimeError("QR_PASS_AUTH_SECRET debe configurarse en producción.")
        logger.warning("QR_PASS_AUTH_SECRET no está configurado; las sesiones demo vencerán al reiniciar la API.")
        configured_secret = secrets.token_bytes(32)
    secret_bytes = configured_secret.encode("utf-8") if isinstance(configured_secret, str) else configured_secret
    if len(secret_bytes) < 32:
        raise RuntimeError("QR_PASS_AUTH_SECRET debe tener al menos 32 bytes.")
    if is_production and (
        not os.getenv("QR_PASS_DEMO_PASSENGER_PASSWORD")
        or not os.getenv("QR_PASS_DEMO_DRIVER_PASSWORD")
    ):
        raise RuntimeError("Las contraseñas de demostración no deben utilizarse en producción.")

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
        database.initialize()
        yield
        database.close()

    application = FastAPI(
        title="QrPass API",
        description=(
            "API REST inicial para explorar QrPass. Incluye autenticación bearer y acceso "
            "al espacio conductor según roles; los movimientos siguen siendo de demostración "
            "y no se procesan pagos reales."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )
    application.state.database = database
    application.state.auth_secret = secret_bytes

    cors_origins = [
        origin.strip()
        for origin in os.getenv(
            "QR_PASS_CORS_ORIGINS",
            "http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000,http://127.0.0.1:8000",
        ).split(",")
        if origin.strip()
    ]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
    )

    @application.exception_handler(DomainError)
    async def domain_error_handler(_: Request, error: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=error.status_code,
            content={"detail": error.detail},
        )

    application.include_router(router)
    return application


app = create_app()
