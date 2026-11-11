from __future__ import annotations
# Este módulo configura FastAPI, conecta la base de datos y carga el router principal.

import os
import sys

# Evita que la consola muestre caracteres mal codificados (mojibake) en Windows.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
import logging
import secrets
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.database import BaseDatos
from app.controllers import router
from app.servicios.comun import ErrorDominio

logger = logging.getLogger(__name__)


def crear_aplicacion(database_url: str | None = None, auth_secret: str | bytes | None = None) -> FastAPI:
    database = BaseDatos(database_url)

    configured_secret = auth_secret or os.getenv("QR_PASS_AUTH_SECRET")
    is_production = os.getenv("QR_PASS_ENV", "").lower() == "production"
    if configured_secret is None:
        if is_production:
            raise RuntimeError("QR_PASS_AUTH_SECRET debe configurarse en producción.")
        logger.warning("QR_PASS_AUTH_SECRET no esta configurado; las sesiones demo venceran al reiniciar la API.")
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

    configured_origins = os.getenv("QR_PASS_CORS_ORIGINS")
    if configured_origins is None:
        # En desarrollo se permite cualquier origen para facilitar demos en red local (celular).
        cors_origins = ["*"] if not is_production else []
    else:
        cors_origins = [origin.strip() for origin in configured_origins.split(",") if origin.strip()]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
    )

    @application.exception_handler(ErrorDominio)
    async def domain_error_handler(_: Request, error: ErrorDominio) -> JSONResponse:
        return JSONResponse(
            status_code=error.status_code,
            content={"detail": error.detail},
            headers={"WWW-Authenticate": "Bearer"} if error.status_code == 401 else None,
        )

    def _traducir_validacion(issue: dict) -> str:
        tipo = str(issue.get("type", ""))
        contexto = issue.get("ctx") or {}
        campo = ".".join(str(part) for part in issue.get("loc", []) if part != "body")
        nombre = campo or "solicitud"

        if tipo == "missing":
            return f"{nombre}: este campo es obligatorio."
        if tipo.startswith("greater_than"):
            limite = contexto.get("gt")
            return f"{nombre}: debe ser mayor a {limite}." if limite is not None else f"{nombre}: el valor es demasiado pequeño."
        if tipo.startswith("greater_than_equal"):
            limite = contexto.get("ge")
            return f"{nombre}: debe ser mayor o igual a {limite}." if limite is not None else f"{nombre}: el valor es demasiado pequeño."
        if tipo.startswith("less_than"):
            limite = contexto.get("lt")
            return f"{nombre}: debe ser menor a {limite}." if limite is not None else f"{nombre}: el valor es demasiado grande."
        if tipo.startswith("less_than_equal"):
            limite = contexto.get("le")
            return f"{nombre}: debe ser menor o igual a {limite}." if limite is not None else f"{nombre}: el valor es demasiado grande."
        if tipo == "string_too_short":
            limite = contexto.get("min_length")
            return f"{nombre}: debe tener al menos {limite} caracteres." if limite is not None else f"{nombre}: el texto es demasiado corto."
        if tipo == "string_too_long":
            limite = contexto.get("max_length")
            return f"{nombre}: debe tener como máximo {limite} caracteres." if limite is not None else f"{nombre}: el texto es demasiado largo."
        if tipo == "string_pattern_mismatch":
            return f"{nombre}: el formato no es válido."
        if tipo.startswith("enum"):
            return f"{nombre}: el valor seleccionado no es válido."
        if tipo == "int_parsing":
            return f"{nombre}: debe ser un número entero."
        if tipo == "float_parsing":
            return f"{nombre}: debe ser un número."
        if tipo == "bool_parsing":
            return f"{nombre}: debe ser verdadero o falso."
        if tipo == "email":
            return f"{nombre}: el correo no tiene un formato válido."
        if tipo.startswith("value_error"):
            mensaje = issue.get("msg", "")
            if "Value error" in mensaje:
                mensaje = mensaje.split("Value error,", 1)[-1].strip()
            return f"{nombre}: {mensaje or 'valor no válido'}."
        return f"{nombre}: {issue.get('msg', 'valor no válido')}."

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, error: RequestValidationError) -> JSONResponse:
        # Convierte errores de validación en mensajes claros para la interfaz.
        errores = []
        for issue in error.errors():
            campo = ".".join(str(part) for part in issue.get("loc", []) if part != "body")
            mensaje = _traducir_validacion(issue)
            errores.append({"campo": campo or "solicitud", "mensaje": mensaje})
        detalle = [f"{item['campo']}: {item['mensaje'].split(':', 1)[-1].strip()}" for item in errores]
        return JSONResponse(
            status_code=422,
            content={
                "detail": [{"msg": mensaje} for mensaje in (detalle if detalle else ["Los datos enviados no son válidos."])],
                "errores": errores,
            },
        )

    @application.exception_handler(Exception)
    async def unexpected_error_handler(_: Request, error: Exception) -> JSONResponse:
        logger.exception("Error inesperado: %s", error)
        return JSONResponse(
            status_code=500,
            content={"detail": "Ocurrió un error inesperado. Intenta de nuevo en unos momentos."},
        )

    application.include_router(router)

    @application.get("/health", include_in_schema=False)
    async def health_root() -> dict[str, str]:
        return {"status": "ok", "service": "qrpass-api", "mode": "demo"}

    # Opcional: servir también la interfaz (carpeta frontend/) desde el mismo origen que la API.
    # Con QR_PASS_SERVE_FRONTEND=1 basta un solo puerto y un solo túnel HTTPS para abrir la app
    # en el celular; el navegador exige HTTPS para permitir la cámara fuera de localhost.
    frontend_dir = Path(__file__).resolve().parents[3] / "frontend"
    serve_frontend = os.getenv("QR_PASS_SERVE_FRONTEND", "").lower() in {"1", "true", "yes"}
    if serve_frontend and frontend_dir.is_dir():
        # Debe registrarse al final: las rutas de la API y /health tienen prioridad.
        application.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
    else:
        if serve_frontend:
            logger.warning("QR_PASS_SERVE_FRONTEND está activo pero no existe la carpeta %s.", frontend_dir)

        @application.get("/", include_in_schema=False)
        async def root() -> dict[str, str]:
            return {"service": "qrpass-api", "docs": "/docs", "health": "/api/v1/health"}

    return application


app = crear_aplicacion()