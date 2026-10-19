from datetime import datetime
from typing import Annotated

from pydantic import Field

from app.dtos.base import EsquemaBase


# Viaje original y ruta nueva solicitados para un traspaso.
class CrearTransbordoSolicitud(EsquemaBase):
    # Identifica el viaje previo y la ruta a la que se solicita transferir.
    # Ambos identificadores deben ser mayores que cero; las reglas de elegibilidad
    # (dueño, tiempo y rutas diferentes) se verifican en el servicio.
    viaje_id: Annotated[int, Field(gt=0, validation_alias="trip_id", serialization_alias="trip_id")]
    ruta_destino_id: Annotated[int, Field(gt=0, validation_alias="destination_route_id", serialization_alias="destination_route_id")]


# Resultado del cambio de ruta asociado al viaje.
class TransbordoRespuesta(EsquemaBase):
    # Confirma el origen/destino y el posible cobro adicional (cero en el demo).
    # Resume el movimiento y deja visibles ambas rutas para la interfaz.
    transbordo_id: int = Field(validation_alias="transfer_id", serialization_alias="transfer_id")
    viaje_origen_id: int = Field(validation_alias="origin_trip_id", serialization_alias="origin_trip_id")
    ruta_origen: str = Field(validation_alias="origin_route", serialization_alias="origin_route")
    ruta_destino_id: int = Field(validation_alias="destination_route_id", serialization_alias="destination_route_id")
    ruta_destino: str = Field(validation_alias="destination_route", serialization_alias="destination_route")
    cobro_adicional: int = Field(default=0, validation_alias="additional_charge", serialization_alias="additional_charge")
    moneda: str = Field(default="COP", validation_alias="currency", serialization_alias="currency")
    creado_en: datetime = Field(validation_alias="created_at", serialization_alias="created_at")
    modo: str = Field(default="demo", validation_alias="mode", serialization_alias="mode")
