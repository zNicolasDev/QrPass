from __future__ import annotations
# Este archivo define los DTOs para el módulo de administración, auditoría y métricas gerenciales.
from pydantic import Field
from app.dtos.base import EsquemaBase


# Resumen consolidado del recaudo y operación del transporte urbano para el Gerente.
class MetricasGerencialesRespuesta(EsquemaBase):
    total_recaudado: int = Field(default=0, validation_alias="total_collected", serialization_alias="total_collected")
    recaudo_efectivo: int = Field(default=0, validation_alias="cash_collected", serialization_alias="cash_collected")
    recaudo_qr: int = Field(default=0, validation_alias="qr_collected", serialization_alias="qr_collected")
    recaudo_tarjeta: int = Field(default=0, validation_alias="card_collected", serialization_alias="card_collected")
    total_viajes: int = Field(default=0, validation_alias="total_trips", serialization_alias="total_trips")
    total_transbordos: int = Field(default=0, validation_alias="total_transfers", serialization_alias="total_transfers")
    turnos_activos: int = Field(default=0, validation_alias="active_shifts", serialization_alias="active_shifts")
    total_usuarios: int = Field(default=0, validation_alias="total_users", serialization_alias="total_users")
    total_rutas: int = Field(default=0, validation_alias="total_routes", serialization_alias="total_routes")


# Confirmación del restablecimiento de saldos y turnos para pruebas de sustentación.
class ReinicioDemoRespuesta(EsquemaBase):
    estado: str = Field(default="ok", validation_alias="status", serialization_alias="status")
    mensaje: str = Field(validation_alias="message", serialization_alias="message")
    saldo_pasajero: int = Field(validation_alias="passenger_balance", serialization_alias="passenger_balance")
