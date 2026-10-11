from pydantic import Field

from app.dtos.base import EsquemaBase


class CuentaRespuesta(EsquemaBase):
    usuario_id: int = Field(validation_alias="user_id", serialization_alias="user_id")
    nombres: str = Field(validation_alias="names", serialization_alias="names")
    saldo_billetera: int = Field(validation_alias="wallet_balance", serialization_alias="wallet_balance")
    moneda: str = Field(default="COP", validation_alias="currency", serialization_alias="currency")
    modo: str = Field(default="demo", validation_alias="mode", serialization_alias="mode")
