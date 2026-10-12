from pydantic import BaseModel, ConfigDict


class EsquemaBase(BaseModel):
    # Todos los DTOs heredan de BaseModel: Pydantic valida tipos y prepara JSON.
    # En Field, validation_alias nombra la clave aceptada al leer el JSON;
    # serialization_alias nombra la clave enviada al devolverlo.
    model_config = ConfigDict(
        # Permite construir DTOs leyendo atributos de objetos, por ejemplo ORM.
        from_attributes=True,
        # Acepta el nombre Python del campo aunque este tenga un alias externo.
        populate_by_name=True,
        # Al responder, usa las claves públicas (por ejemplo, "user_id").
        serialize_by_alias=True,
    )
