from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("wallet_balance >= 0", name="ck_users_wallet_nonnegative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    names: Mapped[str] = mapped_column(String(120), nullable=False)
    username: Mapped[str | None] = mapped_column(String(80), unique=True)
    email: Mapped[str | None] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(256))
    privacy_consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    document_number: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    wallet_balance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    payments: Mapped[list[Payment]] = relationship(back_populates="user")
    qr_codes: Mapped[list[QrCode]] = relationship(back_populates="user")
    cards: Mapped[list[Card]] = relationship(back_populates="user")
    roles: Mapped[list[UserRole]] = relationship(back_populates="user")
    driver: Mapped[Driver | None] = relationship(back_populates="user", uselist=False)


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)

    users: Mapped[list[UserRole]] = relationship(back_populates="role")


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)

    user: Mapped[User] = relationship(back_populates="roles")
    role: Mapped[Role] = relationship(back_populates="users")


class TransportCompany(Base):
    __tablename__ = "transport_companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)

    vehicles: Mapped[list[Vehicle]] = relationship(back_populates="company")


class Route(Base):
    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    fares: Mapped[list[Fare]] = relationship(back_populates="route")
    shifts: Mapped[list[Shift]] = relationship(back_populates="route")
    trips: Mapped[list[Trip]] = relationship(back_populates="route")
    destination_transfers: Mapped[list[Transfer]] = relationship(back_populates="destination_route")


class Fare(Base):
    __tablename__ = "fares"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_fares_amount_positive"),
        CheckConstraint("day_type IN ('weekday', 'weekend')", name="ck_fares_day_type"),
        UniqueConstraint("route_id", "day_type", name="uq_fares_route_day_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id", ondelete="RESTRICT"), nullable=False)
    day_type: Mapped[str] = mapped_column(String(12), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    route: Mapped[Route] = relationship(back_populates="fares")
    trips: Mapped[list[Trip]] = relationship(back_populates="fare")


class Driver(Base):
    __tablename__ = "drivers"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    license_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    user: Mapped[User] = relationship(back_populates="driver")
    shifts: Mapped[list[Shift]] = relationship(back_populates="driver")


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("transport_companies.id", ondelete="RESTRICT"), nullable=False)
    plate: Mapped[str] = mapped_column(String(12), unique=True, nullable=False)

    company: Mapped[TransportCompany] = relationship(back_populates="vehicles")
    shifts: Mapped[list[Shift]] = relationship(back_populates="vehicle")
    boarding_devices: Mapped[list[BoardingDevice]] = relationship(back_populates="vehicle")


class BoardingDevice(Base):
    __tablename__ = "boarding_devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=False)
    serial: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)

    vehicle: Mapped[Vehicle] = relationship(back_populates="boarding_devices")
    sync_events: Mapped[list[OfflineSync]] = relationship(back_populates="device")


class Shift(Base):
    __tablename__ = "shifts"
    __table_args__ = (
        CheckConstraint("ends_at IS NULL OR ends_at >= starts_at", name="ck_shifts_valid_dates"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.user_id", ondelete="RESTRICT"), nullable=False)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=False)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id", ondelete="RESTRICT"), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    cash_counted: Mapped[int | None] = mapped_column(Integer)
    cash_difference: Mapped[int | None] = mapped_column(Integer)

    driver: Mapped[Driver] = relationship(back_populates="shifts")
    vehicle: Mapped[Vehicle] = relationship(back_populates="shifts")
    route: Mapped[Route] = relationship(back_populates="shifts")
    trips: Mapped[list[Trip]] = relationship(back_populates="shift")


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    card_type: Mapped[str] = mapped_column(String(12), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    user: Mapped[User] = relationship(back_populates="cards")
    payments: Mapped[list[Payment]] = relationship(back_populates="card")


class QrCode(Base):
    __tablename__ = "qr_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="qr_codes")
    payments: Mapped[list[Payment]] = relationship(back_populates="qr_code")


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_payments_amount_nonnegative"),
        CheckConstraint("balance_before >= 0", name="ck_payments_balance_before_nonnegative"),
        CheckConstraint("balance_after >= 0", name="ck_payments_balance_after_nonnegative"),
        UniqueConstraint("user_id", "idempotency_key", name="uq_payments_user_idempotency_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(80))
    card_id: Mapped[int | None] = mapped_column(ForeignKey("cards.id", ondelete="RESTRICT"))
    qr_code_id: Mapped[int | None] = mapped_column(ForeignKey("qr_codes.id", ondelete="RESTRICT"))
    method: Mapped[str] = mapped_column(String(20), nullable=False)
    movement_type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_before: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="payments")
    card: Mapped[Card | None] = relationship(back_populates="payments")
    qr_code: Mapped[QrCode | None] = relationship(back_populates="payments")
    trip: Mapped[Trip | None] = relationship(back_populates="payment", uselist=False)


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id", ondelete="RESTRICT"), unique=True, nullable=False)
    shift_id: Mapped[int | None] = mapped_column(ForeignKey("shifts.id", ondelete="RESTRICT"))
    fare_id: Mapped[int] = mapped_column(ForeignKey("fares.id", ondelete="RESTRICT"), nullable=False)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    payment: Mapped[Payment] = relationship(back_populates="trip")
    shift: Mapped[Shift | None] = relationship(back_populates="trips")
    fare: Mapped[Fare] = relationship(back_populates="trips")
    route: Mapped[Route] = relationship(back_populates="trips")
    origin_transfer: Mapped[Transfer | None] = relationship(back_populates="origin_trip", uselist=False)


class Transfer(Base):
    __tablename__ = "transfers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    origin_trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id", ondelete="RESTRICT"), unique=True, nullable=False)
    destination_route_id: Mapped[int] = mapped_column(ForeignKey("routes.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    origin_trip: Mapped[Trip] = relationship(back_populates="origin_transfer")
    destination_route: Mapped[Route] = relationship(back_populates="destination_transfers")


class OfflineSync(Base):
    __tablename__ = "offline_syncs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("boarding_devices.id", ondelete="RESTRICT"), nullable=False)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    device: Mapped[BoardingDevice] = relationship(back_populates="sync_events")
