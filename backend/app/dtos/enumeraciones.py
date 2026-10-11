from enum import Enum


class MedioPago(str, Enum):
    WALLET = "wallet"
    CASH = "cash"
    CARD = "card"


class TipoTarjeta(str, Enum):
    DEBIT = "debit"
    CREDIT = "credit"
