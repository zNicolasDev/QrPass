from pydantic import BaseModel, ConfigDict


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
