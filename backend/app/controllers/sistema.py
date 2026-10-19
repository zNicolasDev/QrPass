from __future__ import annotations
# Este controlador expone el estado de la API, las rutas disponibles y sus tarifas.
import logging
from datetime import date
from typing import Annotated
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import Request
from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.database import obtener_sesion
from app.database import verificar_conexion
from app.dtos import TarifaRespuesta
from app.dtos import EstadoServicioRespuesta
from app.dtos import RutaRespuesta
from app.services import obtener_tarifa_vigente
from app.services import listar_rutas




SessionDependency = Annotated[Session, Depends(obtener_sesion)]
logger = logging.getLogger(__name__)
router = APIRouter()

# Confirma que el proceso de la API esta respondiendo.
@router.get("/health", response_model=EstadoServicioRespuesta, tags=["Sistema"])
def endpoint_estado_salud() -> EstadoServicioRespuesta:
    # Solo confirma que FastAPI está atendiendo; no abre una conexión a la base.
    return EstadoServicioRespuesta(estado="ok", servicio="qrpass-api", modo="demo")

# Comprueba que la base de datos responda a una consulta.
@router.get("/ready", response_model=EstadoServicioRespuesta, tags=["Sistema"], summary="Verificar disponibilidad de la base de datos")
def endpoint_verificar_disponibilidad(request: Request) -> EstadoServicioRespuesta:
    # A diferencia de /health, este endpoint sí pide a database.py probar la conexión.
    try:
        verificar_conexion(request.app.state.database)
    except SQLAlchemyError as error:
        # Un error de conexión se presenta como 503 para indicar indisponibilidad.
        logger.error("La comprobación de disponibilidad de la base de datos falló.", exc_info=error)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La base de datos no está disponible.",
        ) from error
    return EstadoServicioRespuesta(estado="ready", servicio="qrpass-api", modo="demo")

# Devuelve el catálogo de rutas activas.
@router.get("/routes", response_model=list[RutaRespuesta], tags=["Rutas"])
def endpoint_listar_rutas(session: SessionDependency) -> list[RutaRespuesta]:
    # El servicio consulta las rutas activas; Pydantic las transforma al contrato JSON.
    return [RutaRespuesta.model_validate(route) for route in listar_rutas(session)]

# Devuelve las tarifas activas para la fecha indicada.
@router.get("/fares/current", response_model=list[TarifaRespuesta], tags=["Tarifas"])
def endpoint_tarifas_vigentes(
    session: SessionDependency,
    route_id: Annotated[int | None, Query(gt=0)] = None,
    on_date: date | None = None,
) -> list[TarifaRespuesta]:
    # Los filtros vienen de la URL. El servicio decide qué tarifas son vigentes.
    return [TarifaRespuesta.model_validate(fare) for fare in obtener_tarifa_vigente(session, route_id, on_date)]
