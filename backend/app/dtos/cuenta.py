from pydantic import Field

from app.dtos.base import EsquemaBase


# Saldo e identidad básica de la cuenta consultada.
class CuentaRespuesta(EsquemaBase):
    # Vista resumida de la cuenta y su saldo para la interfaz del pasajero.
    # Identifica la cuenta y muestra el nombre y el saldo disponible.
    usuario_id: int = Field(validation_alias="user_id", serialization_alias="user_id")
    nombres: str = Field(validation_alias="names", serialization_alias="names")
    saldo_billetera: int = Field(validation_alias="wallet_balance", serialization_alias="wallet_balance")
    moneda: str = Field(default="COP", validation_alias="currency", serialization_alias="currency")
    modo: str = Field(default="demo", validation_alias="mode", serialization_alias="mode")
