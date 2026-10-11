from datetime import datetime
from typing import Annotated

from pydantic import Field, model_validator

from app.dtos.enumeraciones import TipoTarjeta, MedioPago
from app.dtos.base import EsquemaBase


class AsignacionConductorRespuesta(EsquemaBase):
    nombre_conductor: str = Field(validation_alias="driver_name", serialization_alias="driver_name")
    numero_licencia: str = Field(validation_alias="license_number", serialization_alias="license_number")
    ruta_id: int = Field(validation_alias="route_id", serialization_alias="route_id")
    nombre_ruta: str = Field(validation_alias="route_name", serialization_alias="route_name")
    placa_vehiculo: str = Field(validation_alias="vehicle_plate", serialization_alias="vehicle_plate")
    estado_turno: str = Field(default="demo_assignment", validation_alias="shift_status", serialization_alias="shift_status")
    modo: str = Field(default="demo", validation_alias="mode", serialization_alias="mode")


class MovimientoTurnoRespuesta(EsquemaBase):
    pago_id: int = Field(validation_alias="payment_id", serialization_alias="payment_id")
    nombre_ruta: str = Field(validation_alias="route_name", serialization_alias="route_name")
    medio: str = Field(validation_alias="method", serialization_alias="method")
    monto: int = Field(validation_alias="amount", serialization_alias="amount")
    creado_en: datetime = Field(validation_alias="created_at", serialization_alias="created_at")


class TurnoConductorRespuesta(EsquemaBase):
    turno_id: int = Field(validation_alias="shift_id", serialization_alias="shift_id")
    ruta_id: int = Field(validation_alias="route_id", serialization_alias="route_id")
    nombre_ruta: str = Field(validation_alias="route_name", serialization_alias="route_name")
    placa_vehiculo: str = Field(validation_alias="vehicle_plate", serialization_alias="vehicle_plate")
    estado: str = Field(validation_alias="status", serialization_alias="status")
    inicia_en: datetime = Field(validation_alias="starts_at", serialization_alias="starts_at")
    finaliza_en: datetime | None = Field(default=None, validation_alias="ends_at", serialization_alias="ends_at")
    total_efectivo: int = Field(default=0, validation_alias="cash_total", serialization_alias="cash_total")
    total_qr: int = Field(default=0, validation_alias="qr_total", serialization_alias="qr_total")
    total_tarjeta: int = Field(default=0, validation_alias="card_total", serialization_alias="card_total")
    cantidad_pagos: int = Field(default=0, validation_alias="payment_count", serialization_alias="payment_count")
    movimientos: list[MovimientoTurnoRespuesta] = Field(default_factory=list, validation_alias="entries", serialization_alias="entries")
    efectivo_contado: int | None = Field(default=None, validation_alias="cash_counted", serialization_alias="cash_counted")
    diferencia_efectivo: int | None = Field(default=None, validation_alias="cash_difference", serialization_alias="cash_difference")
    moneda: str = Field(default="COP", validation_alias="currency", serialization_alias="currency")
    modo: str = Field(default="demo", validation_alias="mode", serialization_alias="mode")


class PagoConductorSolicitud(EsquemaBase):
    medio: MedioPago = Field(validation_alias="method", serialization_alias="method")
    tipo_tarjeta: TipoTarjeta | None = Field(default=None, validation_alias="card_type", serialization_alias="card_type")
    clave_idempotencia: Annotated[str, Field(min_length=8, max_length=80, validation_alias="idempotency_key", serialization_alias="idempotency_key")]

    @model_validator(mode="after")
    def validar_pago_conductor(self) -> 'PagoConductorSolicitud':
        if self.medio == MedioPago.WALLET:
            raise ValueError("Los pagos wallet/QR deben validarse escaneando un cÃ³digo.")
        if self.medio == MedioPago.CARD and self.tipo_tarjeta is None:
            raise ValueError("card_type es obligatorio para pagos con tarjeta.")
        if self.medio == MedioPago.CASH and self.tipo_tarjeta is not None:
            raise ValueError("card_type solo se admite para pagos con tarjeta.")
        return self


class ValidacionQrConductorSolicitud(EsquemaBase):
    token: Annotated[str, Field(min_length=20, max_length=512)]
    clave_idempotencia: Annotated[str, Field(min_length=8, max_length=80, validation_alias="idempotency_key", serialization_alias="idempotency_key")]


class CierreTurnoSolicitud(EsquemaBase):
    efectivo_contado: Annotated[int, Field(ge=0, validation_alias="cash_counted", serialization_alias="cash_counted")]


class CierreTurnoRespuesta(EsquemaBase):
    turno: TurnoConductorRespuesta = Field(validation_alias="shift", serialization_alias="shift")
    cerrado: bool = Field(validation_alias="closed", serialization_alias="closed")
