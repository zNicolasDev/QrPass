from datetime import datetime
from typing import Annotated

from pydantic import Field, model_validator

from app.dtos.enumeraciones import TipoTarjeta, MedioPago
from app.dtos.base import EsquemaBase


# Ruta y medio de pago solicitados para registrar un viaje.
class CrearPagoSolicitud(EsquemaBase):
    # Datos que el cliente necesita para solicitar un viaje pagado.
    # Annotated combina el tipo int con restricciones extra definidas por Field.
    # route_id debe ser positivo; method y card_type deben formar una combinación válida.
    ruta_id: Annotated[int, Field(gt=0, validation_alias="route_id", serialization_alias="route_id")]
    medio: MedioPago = Field(validation_alias="method", serialization_alias="method")
    tipo_tarjeta: TipoTarjeta | None = Field(default=None, validation_alias="card_type", serialization_alias="card_type")
    clave_idempotencia: Annotated[str | None, Field(min_length=8, max_length=80, validation_alias="idempotency_key", serialization_alias="idempotency_key")] = None

    @model_validator(mode="after")
    def validar_tipo_tarjeta(self) -> 'CrearPagoSolicitud':
        # Valida la combinación entre medio y tipo de tarjeta, no cada campo aislado.
        if self.medio == MedioPago.CARD and self.tipo_tarjeta is None:
            raise ValueError("card_type es obligatorio para pagos con tarjeta.")
        if self.medio != MedioPago.CARD and self.tipo_tarjeta is not None:
            raise ValueError("card_type solo se admite para pagos con tarjeta.")
        return self


# Resumen del pago y del viaje creado por la API.
class ReciboPago(EsquemaBase):
    # Comprobante de un pago y del viaje que produjo.
    # IDs conectan el pago con su viaje y su ruta.
    pago_id: int = Field(validation_alias="payment_id", serialization_alias="payment_id")
    viaje_id: int = Field(validation_alias="trip_id", serialization_alias="trip_id")
    ruta_id: int = Field(validation_alias="route_id", serialization_alias="route_id")
    nombre_ruta: str = Field(validation_alias="route_name", serialization_alias="route_name")
    # Datos del cobro y saldo resultante que se muestran después de confirmar.
    medio: str = Field(validation_alias="method", serialization_alias="method")
    tipo_tarjeta: str | None = Field(default=None, validation_alias="card_type", serialization_alias="card_type")
    tipo_movimiento: str = Field(validation_alias="movement_type", serialization_alias="movement_type")
    monto: int = Field(validation_alias="amount", serialization_alias="amount")
    moneda: str = Field(default="COP", validation_alias="currency", serialization_alias="currency")
    saldo_billetera: int = Field(validation_alias="wallet_balance", serialization_alias="wallet_balance")
    estado: str = Field(validation_alias="status", serialization_alias="status")
    creado_en: datetime = Field(validation_alias="created_at", serialization_alias="created_at")
    modo: str = Field(default="demo", validation_alias="mode", serialization_alias="mode")


# Movimiento de pago o recarga presentado en el historial.
class HistorialPagosRespuesta(EsquemaBase):
    # Elemento del historial; ruta/viaje pueden faltar en movimientos de recarga.
    # El saldo anterior y posterior permiten ver cómo afectó el movimiento a la billetera.
    pago_id: int = Field(validation_alias="payment_id", serialization_alias="payment_id")
    tipo_movimiento: str = Field(validation_alias="movement_type", serialization_alias="movement_type")
    medio: str = Field(validation_alias="method", serialization_alias="method")
    monto: int = Field(validation_alias="amount", serialization_alias="amount")
    moneda: str = Field(default="COP", validation_alias="currency", serialization_alias="currency")
    saldo_anterior: int = Field(validation_alias="balance_before", serialization_alias="balance_before")
    saldo_posterior: int = Field(validation_alias="balance_after", serialization_alias="balance_after")
    estado: str = Field(validation_alias="status", serialization_alias="status")
    creado_en: datetime = Field(validation_alias="created_at", serialization_alias="created_at")
    viaje_id: int | None = Field(default=None, validation_alias="trip_id", serialization_alias="trip_id")
    ruta_id: int | None = Field(default=None, validation_alias="route_id", serialization_alias="route_id")
    nombre_ruta: str | None = Field(default=None, validation_alias="route_name", serialization_alias="route_name")


# Monto y clave que identifican una solicitud de recarga.
class CrearRecargaSolicitud(EsquemaBase):
    # Solicitud de recarga con monto acotado y clave para evitar duplicados.
    # amount está expresado en pesos y no puede superar el límite de demostración.
    monto: Annotated[int, Field(gt=0, le=500000, validation_alias="amount", serialization_alias="amount")]
    clave_idempotencia: Annotated[str, Field(min_length=8, max_length=80, validation_alias="idempotency_key", serialization_alias="idempotency_key")]


# Resultado de la recarga y saldo que queda en la cuenta.
class ReciboRecarga(EsquemaBase):
    # Comprobante de recarga con el saldo resultante.
    pago_id: int = Field(validation_alias="payment_id", serialization_alias="payment_id")
    tipo_movimiento: str = Field(default="top_up", validation_alias="movement_type", serialization_alias="movement_type")
    monto: int = Field(validation_alias="amount", serialization_alias="amount")
    moneda: str = Field(default="COP", validation_alias="currency", serialization_alias="currency")
    saldo_billetera: int = Field(validation_alias="wallet_balance", serialization_alias="wallet_balance")
    estado: str = Field(validation_alias="status", serialization_alias="status")
    creado_en: datetime = Field(validation_alias="created_at", serialization_alias="created_at")
    modo: str = Field(default="demo", validation_alias="mode", serialization_alias="mode")
