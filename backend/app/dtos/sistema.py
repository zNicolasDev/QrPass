from pydantic import Field

from app.dtos.base import EsquemaBase


class EstadoServicioRespuesta(EsquemaBase):
    estado: str = Field(validation_alias="status", serialization_alias="status")
    servicio: str = Field(validation_alias="service", serialization_alias="service")
    modo: str = Field(validation_alias="mode", serialization_alias="mode")
