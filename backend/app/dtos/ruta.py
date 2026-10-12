from datetime import date

from pydantic import Field

from app.dtos.base import EsquemaBase


class RutaRespuesta(EsquemaBase):
    # Información pública mínima de una ruta.
    id: int
    nombre: str = Field(validation_alias="name", serialization_alias="name")


class TarifaRespuesta(EsquemaBase):
    # Tarifa aplicable a una ruta en una fecha y tipo de día determinados.
    ruta_id: int = Field(validation_alias="route_id", serialization_alias="route_id")
    nombre_ruta: str = Field(validation_alias="route_name", serialization_alias="route_name")
    tipo_dia: str = Field(validation_alias="day_type", serialization_alias="day_type")
    monto: int = Field(validation_alias="amount", serialization_alias="amount")
    moneda: str = Field(default="COP", validation_alias="currency", serialization_alias="currency")
    fecha_servicio: date
