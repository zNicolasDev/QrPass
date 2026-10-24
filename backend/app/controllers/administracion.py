from __future__ import annotations
# Este controlador expone las métricas consolidadas para el rol de Gerente / Administrador
# y la función de reinicio de demostración para sustentaciones académicas.
from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import obtener_sesion
from app.dtos import MetricasGerencialesRespuesta, ReinicioDemoRespuesta
from app.services import obtener_metricas_gerenciales, reiniciar_datos_demo

SessionDependency = Annotated[Session, Depends(obtener_sesion)]
admin_router = APIRouter(prefix="/admin", tags=["Administración y Auditoría"])


# Consulta las métricas globales del recaudo y la operación de transporte.
@admin_router.get(
    "/metrics",
    response_model=MetricasGerencialesRespuesta,
    summary="Consultar métricas globales del sistema (Gerente / Administrador)",
)
def endpoint_metricas_gerenciales(session: SessionDependency) -> MetricasGerencialesRespuesta:
    # El servicio suma y agrupa los pagos y viajes de todas las rutas y turnos.
    metricas = obtener_metricas_gerenciales(session)
    return MetricasGerencialesRespuesta.model_validate(metricas)


# Restablece los saldos y turnos de demostración para iniciar una nueva prueba limpia.
@admin_router.post(
    "/demo/reset",
    response_model=ReinicioDemoRespuesta,
    status_code=status.HTTP_200_OK,
    summary="Restablecer saldos y turnos de demostración",
)
def endpoint_reiniciar_demo(session: SessionDependency) -> ReinicioDemoRespuesta:
    resultado = reiniciar_datos_demo(session)
    return ReinicioDemoRespuesta.model_validate(resultado)
