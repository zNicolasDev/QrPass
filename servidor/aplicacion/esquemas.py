from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


# Estos esquemas marcan el acuerdo entre la persona que usa la app y el
# servidor: lo que aceptamos y lo que devolvemos, no cómo se guarda por dentro.
class PaymentMethod(str, Enum):
    WALLET = "wallet"
    CASH = "cash"
    CARD = "card"


class CardType(str, Enum):
    DEBIT = "debit"
    CREDIT = "credit"


class RouteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class FareRead(BaseModel):
    route_id: int
    route_name: str
    day_type: str
    amount: int
    currency: str = "COP"
    service_date: date


class AccountRead(BaseModel):
    user_id: int
    names: str
    wallet_balance: int
    currency: str = "COP"
    mode: str = "demo"


class LoginCreate(BaseModel):
    username: Annotated[str, Field(min_length=3, max_length=254)]
    password: Annotated[str, Field(min_length=1, max_length=256)]


class PassengerRegistrationCreate(BaseModel):
    names: Annotated[str, Field(min_length=2, max_length=120)]
    email: EmailStr
    password: Annotated[str, Field(min_length=12, max_length=256)]
    privacy_consent: Literal[True]


class AuthUserRead(BaseModel):
    user_id: int
    username: str
    email: EmailStr | None = None
    names: str
    roles: list[str]
    mode: str = "demo"


class LoginRead(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: AuthUserRead


class DriverAssignmentRead(BaseModel):
    driver_name: str
    license_number: str
    route_id: int
    route_name: str
    vehicle_plate: str
    shift_status: str = "demo_assignment"
    mode: str = "demo"


class DriverShiftRead(BaseModel):
    shift_id: int
    route_id: int
    route_name: str
    vehicle_plate: str
    status: str
    starts_at: datetime
    ends_at: datetime | None = None
    cash_total: int = 0
    qr_total: int = 0
    card_total: int = 0
    payment_count: int = 0
    entries: list[DriverShiftEntryRead] = Field(default_factory=list)
    cash_counted: int | None = None
    cash_difference: int | None = None
    currency: str = "COP"
    mode: str = "demo"


class DriverShiftEntryRead(BaseModel):
    payment_id: int
    route_name: str
    method: str
    amount: int
    created_at: datetime


class DriverPaymentCreate(BaseModel):
    method: PaymentMethod
    card_type: CardType | None = None
    idempotency_key: Annotated[str, Field(min_length=8, max_length=80)]

    @model_validator(mode="after")
    def validate_driver_payment(self) -> DriverPaymentCreate:
        # Un QR no se registra como cobro manual: necesita su propio recorrido
        # de validación para comprobarlo y marcarlo como usado.
        if self.method == PaymentMethod.WALLET:
            raise ValueError("Los pagos wallet/QR deben validarse escaneando un código.")
        if self.method == PaymentMethod.CARD and self.card_type is None:
            raise ValueError("card_type es obligatorio para pagos con tarjeta.")
        if self.method == PaymentMethod.CASH and self.card_type is not None:
            raise ValueError("card_type solo se admite para pagos con tarjeta.")
        return self


class DriverQrValidateCreate(BaseModel):
    token: Annotated[str, Field(min_length=20, max_length=512)]
    idempotency_key: Annotated[str, Field(min_length=8, max_length=80)]


class ShiftCloseRead(BaseModel):
    shift: DriverShiftRead
    closed: bool


class DriverShiftCloseCreate(BaseModel):
    cash_counted: Annotated[int, Field(ge=0)]


class QrCreate(BaseModel):
    route_id: Annotated[int, Field(gt=0)]
    validity_minutes: Annotated[int, Field(default=15, ge=1, le=15)]


class QrRead(BaseModel):
    qr_id: int
    token: str
    status: str
    created_at: datetime
    expires_at: datetime
    scannable: bool = True
    image_data_uri: str
    mode: str = "demo"


class PaymentCreate(BaseModel):
    route_id: Annotated[int, Field(gt=0)]
    method: PaymentMethod
    card_type: CardType | None = None
    idempotency_key: Annotated[str | None, Field(min_length=8, max_length=80)] = None

    @model_validator(mode="after")
    def validate_card_type(self) -> PaymentCreate:
        if self.method == PaymentMethod.CARD and self.card_type is None:
            raise ValueError("card_type es obligatorio para pagos con tarjeta.")
        if self.method != PaymentMethod.CARD and self.card_type is not None:
            raise ValueError("card_type solo se admite para pagos con tarjeta.")
        return self


class PaymentReceipt(BaseModel):
    payment_id: int
    trip_id: int
    route_id: int
    route_name: str
    method: str
    card_type: str | None = None
    movement_type: str
    amount: int
    currency: str = "COP"
    wallet_balance: int
    status: str
    created_at: datetime
    mode: str = "demo"


class TopUpCreate(BaseModel):
    amount: Annotated[int, Field(gt=0, le=500000)]
    idempotency_key: Annotated[str, Field(min_length=8, max_length=80)]


class TopUpReceipt(BaseModel):
    payment_id: int
    movement_type: str = "top_up"
    amount: int
    currency: str = "COP"
    wallet_balance: int
    status: str
    created_at: datetime
    mode: str = "demo"


class TripRead(BaseModel):
    trip_id: int
    route_id: int
    route_name: str
    payment_id: int
    method: str
    movement_type: str
    amount: int
    currency: str = "COP"
    status: str
    created_at: datetime
    transferred_to: str | None = None


class PaymentHistoryRead(BaseModel):
    payment_id: int
    movement_type: str
    method: str
    amount: int
    currency: str = "COP"
    balance_before: int
    balance_after: int
    status: str
    created_at: datetime
    trip_id: int | None = None
    route_id: int | None = None
    route_name: str | None = None


class TransferCreate(BaseModel):
    trip_id: Annotated[int, Field(gt=0)]
    destination_route_id: Annotated[int, Field(gt=0)]


class TransferRead(BaseModel):
    transfer_id: int
    origin_trip_id: int
    origin_route: str
    destination_route_id: int
    destination_route: str
    additional_charge: int = 0
    currency: str = "COP"
    created_at: datetime
    mode: str = "demo"


class HealthRead(BaseModel):
    status: str
    service: str
    mode: str
