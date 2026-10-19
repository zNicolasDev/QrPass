from datetime import datetime

from pydantic import Field

from app.dtos.base import EsquemaBase


# Datos de un viaje que se muestran en listas y detalles.
class ViajeRespuesta(EsquemaBase):
    # Vista de un viaje; combina datos que internamente pertenecen a pago y ruta.
    # Los IDs permiten relacionarlo; los demás campos sirven para mostrar el historial.
    viaje_id: int = Field(validation_alias="trip_id", serialization_alias="trip_id")
    ruta_id: int = Field(validation_alias="route_id", serialization_alias="route_id")
    nombre_ruta: str = Field(validation_alias="route_name", serialization_alias="route_name")
    pago_id: int = Field(validation_alias="payment_id", serialization_alias="payment_id")
    medio: str = Field(validation_alias="method", serialization_alias="method")
    tipo_movimiento: str = Field(validation_alias="movement_type", serialization_alias="movement_type")
    monto: int = Field(validation_alias="amount", serialization_alias="amount")
    moneda: str = Field(default="COP", validation_alias="currency", serialization_alias="currency")
    estado: str = Field(validation_alias="status", serialization_alias="status")
    creado_en: datetime = Field(validation_alias="created_at", serialization_alias="created_at")
    transferido_a: str | None = Field(default=None, validation_alias="transferred_to", serialization_alias="transferred_to")
