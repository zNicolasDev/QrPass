from __future__ import annotations
# Este controlador expone las métricas consolidadas para el rol de Administrador.
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import obtener_sesion
from app.dtos import MetricasGerencialesRespuesta
from app.models import Usuario
from app.seguridad.auth import requerir_rol
from app.servicios.administracion import obtener_metricas_gerenciales

SessionDependency = Annotated[Session, Depends(obtener_sesion)]
admin_router = APIRouter(prefix="/admin", tags=["Administración y Auditoría"])


# Consulta las métricas globales del recaudo y la operación de transporte.
@admin_router.get(
    "/metrics",
    response_model=MetricasGerencialesRespuesta,
    summary="Consultar métricas globales del sistema (Administrador)",
)
def endpoint_metricas_gerenciales(
    _user: Annotated[Usuario, Depends(requerir_rol("ADMIN"))],
    session: SessionDependency,
) -> MetricasGerencialesRespuesta:
    # El permiso ADMIN se comprueba antes de calcular los totales.
    # El servicio suma y agrupa los pagos y viajes de todas las rutas y turnos.
    metricas = obtener_metricas_gerenciales(session)
    return MetricasGerencialesRespuesta.model_validate(metricas)
