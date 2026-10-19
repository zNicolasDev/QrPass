from datetime import datetime
from typing import Annotated

from pydantic import Field

from app.dtos.base import EsquemaBase


class ValidacionQrPasajeroSolicitud(EsquemaBase):
    # El pasajero envía el contenido leído del QR que muestra el bus.
    token: Annotated[str, Field(min_length=20, max_length=512)]
    # Si la respuesta tarda, la misma clave evita cobrar dos veces.
    clave_idempotencia: Annotated[str, Field(min_length=8, max_length=80, validation_alias="idempotency_key", serialization_alias="idempotency_key")]


# QR temporal que presenta el bus durante su turno activo.
class CodigoQrRespuesta(EsquemaBase):
    # La pantalla del bus muestra esta imagen para que el pasajero la escanee.
    codigo_qr_id: int = Field(validation_alias="qr_id", serialization_alias="qr_id")
    token: str
    # Estado y fechas indican si el código del turno todavía puede usarse.
    estado: str = Field(validation_alias="status", serialization_alias="status")
    creado_en: datetime = Field(validation_alias="created_at", serialization_alias="created_at")
    vence_en: datetime = Field(validation_alias="expires_at", serialization_alias="expires_at")
    # La imagen viene lista para mostrar en el navegador como data URI.
    escaneable: bool = Field(default=True, validation_alias="scannable", serialization_alias="scannable")
    imagen_data_uri: str = Field(validation_alias="image_data_uri", serialization_alias="image_data_uri")
    modo: str = Field(default="demo", validation_alias="mode", serialization_alias="mode")
