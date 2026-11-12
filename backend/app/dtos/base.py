from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, field_validator

# Hora oficial de la aplicación: Colombia (UTC-5, sin horario de verano).
# La base guarda las fechas en UTC; al responder se muestran en hora de Bogotá.
ZONA_HORARIA_APP = ZoneInfo("America/Bogota")


# Configuración compartida para validar y serializar los DTOs.
class EsquemaBase(BaseModel):
    # Todos los DTOs heredan de BaseModel: Pydantic valida tipos y prepara JSON.
    # En cada DTO, Field puede poner límites y configurar nombres públicos.
    # validation_alias indica la clave JSON que se acepta; serialization_alias
    # indica la clave que se devuelve. Así usamos Python en español y JSON en inglés.
    model_config = ConfigDict(
        # Permite construir DTOs leyendo atributos de objetos, por ejemplo ORM.
        from_attributes=True,
        # Acepta el nombre Python del campo aunque este tenga un alias externo.
        populate_by_name=True,
        # Al responder, usa las claves públicas (por ejemplo, "user_id").
        serialize_by_alias=True,
    )

    @field_validator("*", mode="after")
    @classmethod
    def _fechas_en_hora_de_bogota(cls, value):
        # Toda fecha que sale por la API lleva su desfase explícito (-05:00).
        if isinstance(value, datetime):
            # SQLite devuelve las fechas sin zona; como se guardan en UTC, se leen como UTC.
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return value.astimezone(ZONA_HORARIA_APP)
        return value
