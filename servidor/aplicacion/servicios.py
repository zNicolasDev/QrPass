from __future__ import annotations

import base64
import hashlib
import hmac
import io
import json
import secrets
from datetime import date, datetime, timedelta, timezone
from typing import TypedDict
from zoneinfo import ZoneInfo

import holidays
import qrcode
from qrcode.image.svg import SvgPathImage
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, joinedload

from aplicacion.esquemas import PaymentCreate, PaymentMethod, TopUpCreate, TransferCreate
from aplicacion.modelos import Fare, Payment, QrCode, Route, Shift, Transfer, Trip, User


# Aquí están las decisiones que una persona esperaría que siempre se cumplan,
# use la pantalla actual o un cliente futuro distinto.
IBAGUE_TIMEZONE = ZoneInfo("America/Bogota")


class ShiftEntrySummary(TypedDict):
    payment_id: int
    route_name: str
    method: str
    amount: int
    created_at: datetime


class DriverShiftSummary(TypedDict):
    shift: Shift
    cash: int
    qr: int
    card: int
    payment_count: int
    entries: list[ShiftEntrySummary]


class DomainError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def service_now() -> datetime:
    return datetime.now(timezone.utc)


def service_date() -> date:
    return datetime.now(IBAGUE_TIMEZONE).date()


def day_type_for(day: date) -> str:
    # El día del servicio se entiende según Ibagué; no según la zona horaria
    # del servidor o del celular que hizo la solicitud.
    return "weekend" if day.weekday() == 6 or day in holidays.country_holidays("CO", years=day.year) else "weekday"


def get_demo_user(session: Session) -> User:
    user = session.get(User, 1)
    if user is None or user.status != "active":
        raise DomainError(404, "La cuenta de demostración no existe o está inactiva.")
    return user


def list_routes(session: Session) -> list[Route]:
    statement = select(Route).where(Route.active.is_(True)).order_by(Route.id)
    return list(session.scalars(statement))


def get_current_fare(session: Session, route_id: int | None, on_date: date | None = None) -> list[dict[str, object]]:
    requested_date = on_date or service_date()
    day_type = day_type_for(requested_date)
    statement = (
        select(Fare)
        .options(joinedload(Fare.route))
        .join(Fare.route)
        .where(Fare.active.is_(True), Route.active.is_(True), Fare.day_type == day_type)
        .order_by(Route.id)
    )
    if route_id is not None:
        statement = statement.where(Fare.route_id == route_id)

    fares = list(session.scalars(statement))
    if route_id is not None and not fares:
        raise DomainError(404, "No se encontró una tarifa activa para la ruta indicada.")
    return [
        {
            "route_id": fare.route_id,
            "route_name": fare.route.name,
            "day_type": fare.day_type,
            "amount": fare.amount,
            "service_date": requested_date,
        }
        for fare in fares
    ]


def _encode_qr_payload(payload: dict[str, object]) -> str:
    serialized = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(serialized).rstrip(b"=").decode("ascii")


def _decode_qr_payload(encoded: str) -> dict[str, object]:
    payload = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
    decoded = json.loads(payload)
    if not isinstance(decoded, dict):
        raise ValueError("QR payload must be an object")
    return decoded


def qr_image_data_uri(token: str) -> str:
    code = qrcode.QRCode(box_size=8, border=4, image_factory=SvgPathImage)
    code.add_data(token)
    code.make(fit=True)
    image = code.make_image(fill_color="#173f31", back_color="#ffffff")
    buffer = io.BytesIO()
    image.save(buffer)
    encoded_image = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded_image}"


def create_qr(
    session: Session,
    user: User,
    route_id: int,
    validity_minutes: int,
    signing_secret: bytes,
) -> QrCode:
    route = _active_route(session, route_id)
    fare = _fare_for_route(session, route.id)
    if user.wallet_balance < fare.amount:
        raise DomainError(409, "Saldo insuficiente para generar un código de viaje.")
    now = service_now()
    session.execute(
        update(QrCode)
        .where(QrCode.user_id == user.id, QrCode.status == "active")
        .values(status="revoked")
    )
    qr_code = QrCode(
        user_id=user.id,
        token=secrets.token_urlsafe(48),
        status="active",
        created_at=now,
        expires_at=now + timedelta(minutes=validity_minutes),
    )
    session.add(qr_code)
    session.flush()
    payload = {
        "v": 1,
        "qr_id": qr_code.id,
        "sub": user.id,
        "route_id": route.id,
        "exp": int(qr_code.expires_at.timestamp()),
        "jti": secrets.token_urlsafe(18),
    }
    encoded_payload = _encode_qr_payload(payload)
    signature = hmac.new(signing_secret, encoded_payload.encode("ascii"), hashlib.sha256).hexdigest()
    qr_code.token = f"QRP1.{encoded_payload}.{signature}"
    session.commit()
    session.refresh(qr_code)
    return qr_code


def _active_route(session: Session, route_id: int) -> Route:
    route = session.scalar(select(Route).where(Route.id == route_id, Route.active.is_(True)))
    if route is None:
        raise DomainError(404, "La ruta solicitada no existe o está inactiva.")
    return route


def _fare_for_route(session: Session, route_id: int) -> Fare:
    day_type = day_type_for(service_date())
    fare = session.scalar(select(Fare).where(
        Fare.route_id == route_id,
        Fare.day_type == day_type,
        Fare.active.is_(True),
    ))
    if fare is None:
        raise DomainError(404, "La ruta no tiene una tarifa vigente.")
    return fare


def create_payment(session: Session, user: User, request: PaymentCreate) -> tuple[Payment, Trip, int]:
    if request.idempotency_key:
        # Si la conexión se corta y la pantalla reintenta, la persona no debe
        # pagar dos veces por haber pulsado una sola vez.
        prior = session.scalar(select(Payment).where(
            Payment.user_id == user.id,
            Payment.idempotency_key == request.idempotency_key,
        ))
        if prior is not None:
            if prior.method != request.method.value and prior.method != (
                f"card_{request.card_type.value}" if request.card_type else request.method.value
            ):
                raise DomainError(409, "La clave de idempotencia ya se usó para otro pago.")
            if prior.trip is None:
                raise DomainError(409, "El pago previo no tiene un tiquete asociado.")
            if prior.trip.route_id != request.route_id:
                raise DomainError(409, "La clave de idempotencia ya se usó para otra ruta.")
            return prior, prior.trip, prior.balance_after
    route = _active_route(session, request.route_id)
    fare = _fare_for_route(session, route.id)
    now = service_now()
    is_wallet_payment = request.method == PaymentMethod.WALLET
    balance_before = user.wallet_balance
    balance_after = balance_before

    if is_wallet_payment:
        # El saldo se descuenta con una condición en la misma operación: dos
        # solicitudes simultáneas no pueden gastar el mismo saldo disponible.
        new_balance = session.scalar(
            update(User)
            .where(User.id == user.id, User.status == "active", User.wallet_balance >= fare.amount)
            .values(wallet_balance=User.wallet_balance - fare.amount)
            .returning(User.wallet_balance)
        )
        if new_balance is None:
            session.rollback()
            raise DomainError(409, "Saldo insuficiente para realizar el viaje.")
        balance_after = new_balance
        payment_method = "wallet"
    elif request.method == PaymentMethod.CASH:
        payment_method = "cash"
    else:
        if request.card_type is None:
            raise DomainError(422, "El método tarjeta requiere indicar débito o crédito.")
        payment_method = f"card_{request.card_type.value}"

    payment = Payment(
        user_id=user.id,
        method=payment_method,
        movement_type="fare_payment",
        amount=fare.amount,
        idempotency_key=request.idempotency_key,
        balance_before=balance_before,
        balance_after=balance_after,
        status="completed_demo",
        created_at=now,
    )
    session.add(payment)
    session.flush()
    trip = Trip(
        payment_id=payment.id,
        fare_id=fare.id,
        route_id=route.id,
        created_at=now,
    )
    session.add(trip)
    # El pago y el viaje son una sola promesa: o quedan guardados ambos o no
    # queda ninguno, para no mostrar un cobro sin un viaje (ni al revés).
    session.commit()
    session.refresh(payment)
    session.refresh(trip)
    return payment, trip, balance_after


def create_top_up(session: Session, user: User, request: TopUpCreate) -> Payment:
    prior = session.scalar(select(Payment).where(
        Payment.user_id == user.id,
        Payment.idempotency_key == request.idempotency_key,
    ))
    if prior is not None:
        if prior.movement_type != "top_up" or prior.amount != request.amount:
            raise DomainError(409, "La clave de idempotencia ya se usó para otra operación.")
        return prior

    now = service_now()
    balance_after = session.scalar(
        update(User)
        .where(User.id == user.id, User.status == "active")
        .values(wallet_balance=User.wallet_balance + request.amount)
        .returning(User.wallet_balance)
    )
    if balance_after is None:
        session.rollback()
        raise DomainError(401, "La cuenta no está activa.")
    payment = Payment(
        user_id=user.id,
        idempotency_key=request.idempotency_key,
        method="wallet",
        movement_type="top_up",
        amount=request.amount,
        balance_before=balance_after - request.amount,
        balance_after=balance_after,
        status="completed_demo",
        created_at=now,
    )
    session.add(payment)
    session.commit()
    session.refresh(payment)
    return payment


def list_trips(session: Session, user: User) -> list[Trip]:
    statement = (
        select(Trip)
        .join(Trip.payment)
        .options(joinedload(Trip.route), joinedload(Trip.payment), joinedload(Trip.origin_transfer).joinedload(Transfer.destination_route))
        .where(Payment.user_id == user.id)
        .order_by(Trip.created_at.desc(), Trip.id.desc())
    )
    return list(session.scalars(statement))


def get_trip(session: Session, user: User, trip_id: int) -> Trip:
    trip = session.scalar(
        select(Trip)
        .join(Trip.payment)
        .options(
            joinedload(Trip.route),
            joinedload(Trip.payment),
            joinedload(Trip.origin_transfer).joinedload(Transfer.destination_route),
        )
        .where(Trip.id == trip_id, Payment.user_id == user.id)
    )
    if trip is None:
        raise DomainError(404, "No se encontró el viaje solicitado.")
    return trip


def list_payments(session: Session, user: User) -> list[Payment]:
    statement = (
        select(Payment)
        .options(joinedload(Payment.trip).joinedload(Trip.route))
        .where(Payment.user_id == user.id)
        .order_by(Payment.created_at.desc(), Payment.id.desc())
    )
    return list(session.scalars(statement))


def create_transfer(session: Session, user: User, request: TransferCreate) -> Transfer:
    # El traspaso no crea otro pago: enlaza el viaje ya pagado con otra ruta
    # y deja intacto el registro que la persona puede consultar después.
    origin_trip = session.scalar(
        select(Trip)
        .join(Trip.payment)
        .options(joinedload(Trip.route), joinedload(Trip.payment))
        .where(Trip.id == request.trip_id, Payment.user_id == user.id)
    )
    if origin_trip is None:
        raise DomainError(404, "No se encontró el viaje pagado indicado.")
    if origin_trip.payment.movement_type != "fare_payment":
        raise DomainError(409, "Solo se puede transferir un pago de pasaje.")
    if origin_trip.origin_transfer is not None:
        raise DomainError(409, "Este viaje ya fue transferido.")
    trip_created_at = origin_trip.created_at
    if trip_created_at.tzinfo is None:
        trip_created_at = trip_created_at.replace(tzinfo=timezone.utc)
    if service_now() - trip_created_at > timedelta(minutes=20):
        raise DomainError(409, "El tiempo límite de 20 minutos para el traspaso venció.")

    destination = _active_route(session, request.destination_route_id)
    if destination.id == origin_trip.route_id:
        raise DomainError(422, "La ruta de destino debe ser distinta a la ruta original.")
    _fare_for_route(session, destination.id)

    transfer = Transfer(
        origin_trip_id=origin_trip.id,
        destination_route_id=destination.id,
        created_at=service_now(),
    )
    session.add(transfer)
    session.commit()
    session.refresh(transfer)
    return transfer


def active_driver_shift(session: Session, driver: User) -> Shift | None:
    return session.scalar(
        select(Shift)
        .options(joinedload(Shift.route), joinedload(Shift.vehicle))
        .where(Shift.driver_id == driver.id, Shift.status == "active", Shift.ends_at.is_(None))
        .order_by(Shift.starts_at.desc(), Shift.id.desc())
    )


def assigned_driver_shift(session: Session, driver: User) -> Shift | None:
    return session.scalar(
        select(Shift)
        .options(joinedload(Shift.route), joinedload(Shift.vehicle))
        .where(
            Shift.driver_id == driver.id,
            Shift.status.in_(("assigned", "active")),
            Shift.ends_at.is_(None),
        )
        .order_by(Shift.starts_at.desc(), Shift.id.desc())
    )


def _assert_driver_route(shift: Shift, route_id: int) -> None:
    if shift.route_id != route_id:
        raise DomainError(409, "El código o pago no corresponde a la ruta asignada al turno.")


def redeem_qr(
    session: Session,
    driver: User,
    token: str,
    signing_secret: bytes,
    idempotency_key: str,
) -> tuple[Payment, Trip, int]:
    # Primero comprobamos que el código sea auténtico; el texto de un QR puede
    # copiarse, así que nunca se confía en lo que afirma la imagen por sí sola.
    try:
        prefix, encoded_payload, signature = token.split(".")
        if prefix != "QRP1":
            raise ValueError("Unsupported QR token version")
        expected = hmac.new(signing_secret, encoded_payload.encode("ascii"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError("Invalid QR signature")
        payload = _decode_qr_payload(encoded_payload)
        qr_id = payload.get("qr_id")
        user_id = payload.get("sub")
        route_id = payload.get("route_id")
        expires_at = payload.get("exp")
        if (
            not isinstance(qr_id, int) or isinstance(qr_id, bool)
            or not isinstance(user_id, int) or isinstance(user_id, bool)
            or not isinstance(route_id, int) or isinstance(route_id, bool)
            or not isinstance(expires_at, int) or isinstance(expires_at, bool)
        ):
            raise ValueError("Invalid QR claims")
    except (ValueError, KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
        raise DomainError(422, "El código QR no es válido.") from None

    prior = session.scalar(select(Payment).where(
        Payment.user_id == user_id,
        Payment.idempotency_key == idempotency_key,
    ))
    if prior is not None:
        if prior.qr_code_id != qr_id or prior.trip is None:
            raise DomainError(409, "La clave de idempotencia ya se usó para otra operación.")
        return prior, prior.trip, prior.balance_after

    if expires_at <= int(service_now().timestamp()):
        raise DomainError(410, "El código QR expiró.")
    shift = active_driver_shift(session, driver)
    if shift is None:
        raise DomainError(409, "No hay un turno de conductor activo.")
    _assert_driver_route(shift, route_id)

    qr_code = session.scalar(
        select(QrCode).where(
            QrCode.id == qr_id,
            QrCode.user_id == user_id,
            QrCode.token == token,
            QrCode.status == "active",
            QrCode.expires_at > service_now(),
        )
    )
    if qr_code is None:
        raise DomainError(409, "El código ya fue usado, revocado o no existe.")
    passenger = session.get(User, user_id)
    if passenger is None or passenger.status != "active":
        raise DomainError(401, "La cuenta asociada al código no está activa.")

    fare = _fare_for_route(session, route_id)
    now = service_now()
    balance_before = passenger.wallet_balance
    consumed = session.scalar(
        update(QrCode)
        .where(QrCode.id == qr_code.id, QrCode.status == "active", QrCode.expires_at > now)
        .values(status="consumed")
        .returning(QrCode.id)
        .execution_options(synchronize_session=False)
    )
    if consumed is None:
        session.rollback()
        raise DomainError(409, "El código ya fue utilizado.")
    balance_after = session.scalar(
        update(User)
        .where(User.id == passenger.id, User.status == "active", User.wallet_balance >= fare.amount)
        .values(wallet_balance=User.wallet_balance - fare.amount)
        .returning(User.wallet_balance)
    )
    if balance_after is None:
        session.rollback()
        raise DomainError(409, "Saldo insuficiente para validar el código QR.")
    payment = Payment(
        user_id=passenger.id,
        qr_code_id=qr_code.id,
        idempotency_key=idempotency_key,
        method="wallet",
        movement_type="fare_payment",
        amount=fare.amount,
        balance_before=balance_before,
        balance_after=balance_after,
        status="completed_demo",
        created_at=now,
    )
    session.add(payment)
    session.flush()
    trip = Trip(
        payment_id=payment.id,
        shift_id=shift.id,
        fare_id=fare.id,
        route_id=route_id,
        created_at=now,
    )
    session.add(trip)
    # Consumir QR, descontar saldo y registrar el viaje forman una sola
    # experiencia para el pasajero; un fallo debe dejar el código utilizable.
    session.commit()
    session.refresh(payment)
    session.refresh(trip)
    return payment, trip, balance_after


def record_driver_payment(
    session: Session,
    driver: User,
    method: PaymentMethod,
    card_type: str | None,
    idempotency_key: str,
) -> tuple[Payment, Trip, int]:
    # El recaudo de efectivo/tarjeta se atribuye al turno activo, no a un
    # turno elegido por la interfaz ni a un historial separado del cierre.
    shift = active_driver_shift(session, driver)
    if shift is None:
        raise DomainError(409, "No hay un turno de conductor activo.")
    prior = session.scalar(select(Payment).where(
        Payment.user_id == driver.id,
        Payment.idempotency_key == idempotency_key,
    ))
    if prior is not None:
        expected_method = f"card_{card_type}" if method == PaymentMethod.CARD and card_type else method.value
        if (
            prior.trip is None
            or prior.movement_type != "fare_payment"
            or prior.method != expected_method
            or prior.trip.shift_id != shift.id
        ):
            raise DomainError(409, "La clave de idempotencia ya se usó para otra operación.")
        return prior, prior.trip, prior.balance_after

    fare = _fare_for_route(session, shift.route_id)
    payment_method = f"card_{card_type}" if method == PaymentMethod.CARD and card_type else method.value
    now = service_now()
    balance = driver.wallet_balance
    payment = Payment(
        user_id=driver.id,
        idempotency_key=idempotency_key,
        method=payment_method,
        movement_type="fare_payment",
        amount=fare.amount,
        balance_before=balance,
        balance_after=balance,
        status="completed_demo",
        created_at=now,
    )
    session.add(payment)
    session.flush()
    trip = Trip(
        payment_id=payment.id,
        shift_id=shift.id,
        fare_id=fare.id,
        route_id=shift.route_id,
        created_at=now,
    )
    session.add(trip)
    session.commit()
    session.refresh(payment)
    session.refresh(trip)
    return payment, trip, balance


def _summarize_driver_shift(session: Session, shift: Shift) -> DriverShiftSummary:
    rows = session.execute(
        select(Payment.method, func.sum(Payment.amount), func.count(Payment.id))
        .join(Trip, Trip.payment_id == Payment.id)
        .where(Trip.shift_id == shift.id, Payment.movement_type == "fare_payment")
        .group_by(Payment.method)
    ).all()
    entries = session.execute(
        select(Payment, Trip)
        .join(Trip, Trip.payment_id == Payment.id)
        .options(joinedload(Trip.route))
        .where(Trip.shift_id == shift.id, Payment.movement_type == "fare_payment")
        .order_by(Payment.created_at.desc(), Payment.id.desc())
    ).all()
    totals = {"cash": 0, "qr": 0, "card": 0, "payment_count": 0}
    for method, amount, count in rows:
        if method == "cash":
            totals["cash"] = int(amount or 0)
        elif method == "wallet":
            totals["qr"] = int(amount or 0)
        elif method.startswith("card_"):
            totals["card"] += int(amount or 0)
        totals["payment_count"] += int(count or 0)
    return {
        "shift": shift,
        "cash": totals["cash"],
        "qr": totals["qr"],
        "card": totals["card"],
        "payment_count": totals["payment_count"],
        "entries": [
            {
                "payment_id": payment.id,
                "route_name": trip.route.name,
                "method": payment.method,
                "amount": payment.amount,
                "created_at": payment.created_at,
            }
            for payment, trip in entries
        ],
    }


def driver_shift_summary(session: Session, driver: User) -> DriverShiftSummary | None:
    shift = active_driver_shift(session, driver)
    return _summarize_driver_shift(session, shift) if shift is not None else None


def driver_shift_history(session: Session, driver: User, limit: int = 20) -> list[DriverShiftSummary]:
    shifts = session.scalars(
        select(Shift)
        .options(joinedload(Shift.route), joinedload(Shift.vehicle))
        .where(Shift.driver_id == driver.id, Shift.status == "closed")
        .order_by(Shift.ends_at.desc(), Shift.id.desc())
        .limit(limit)
    )
    return [_summarize_driver_shift(session, shift) for shift in shifts]


def close_driver_shift(session: Session, driver: User, cash_counted: int) -> DriverShiftSummary:
    summary = driver_shift_summary(session, driver)
    if summary is None:
        raise DomainError(409, "No hay un turno activo para cerrar.")
    shift = summary["shift"]
    if not isinstance(shift, Shift):
        raise RuntimeError("La consulta de turno devolvió un tipo inesperado.")
    shift.ends_at = service_now()
    shift.status = "closed"
    shift.cash_counted = cash_counted
    # La diferencia compara lo que el sistema esperaba con lo que el conductor
    # contó; no intenta afirmar que el dinero físico fue verificado.
    shift.cash_difference = cash_counted - int(summary["cash"])
    session.commit()
    session.refresh(shift)
    return summary
