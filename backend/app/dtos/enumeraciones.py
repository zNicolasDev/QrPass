from enum import Enum


class MedioPago(str, Enum):
    # str permite validar/serializar estos valores como cadenas JSON.
    WALLET = "wallet"
    CASH = "cash"
    CARD = "card"


class TipoTarjeta(str, Enum):
    # Opciones permitidas cuando el medio de pago es tarjeta.
    DEBIT = "debit"
    CREDIT = "credit"
