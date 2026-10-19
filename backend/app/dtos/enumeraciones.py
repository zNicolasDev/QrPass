from enum import Enum


# Medios de pago aceptados por las solicitudes.
class MedioPago(str, Enum):
    # str permite validar/serializar estos valores como cadenas JSON.
    WALLET = "wallet"
    CASH = "cash"
    CARD = "card"


# Tipos de tarjeta aceptados cuando el medio es tarjeta.
class TipoTarjeta(str, Enum):
    # Opciones permitidas cuando el medio de pago es tarjeta.
    DEBIT = "debit"
    CREDIT = "credit"
