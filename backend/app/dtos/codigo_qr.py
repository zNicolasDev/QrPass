from datetime import datetime
from typing import Annotated

from pydantic import Field

from app.dtos.base import EsquemaBase


class CrearCodigoQrSolicitud(EsquemaBase):
    ruta_id: Annotated[int, Field(gt=0, validation_alias="route_id", serialization_alias="route_id")]
    vigencia_minutos: Annotated[int, Field(default=15, ge=1, le=15, validation_alias="validity_minutes", serialization_alias="validity_minutes")]


class CodigoQrRespuesta(EsquemaBase):
    codigo_qr_id: int = Field(validation_alias="qr_id", serialization_alias="qr_id")
    token: str
    estado: str = Field(validation_alias="status", serialization_alias="status")
    creado_en: datetime = Field(validation_alias="created_at", serialization_alias="created_at")
    vence_en: datetime = Field(validation_alias="expires_at", serialization_alias="expires_at")
    escaneable: bool = Field(default=True, validation_alias="scannable", serialization_alias="scannable")
    imagen_data_uri: str = Field(validation_alias="image_data_uri", serialization_alias="image_data_uri")
    modo: str = Field(default="demo", validation_alias="mode", serialization_alias="mode")
