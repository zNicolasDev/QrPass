from __future__ import annotations

import datetime
import logging
from datetime import date
import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from aplicacion.sesion import (
    ACCESS_TOKEN_SECONDS,
    AuthenticatedUser,
    create_access_token,
    require_role,
    verify_password,
)
from aplicacion.base_datos import get_session
from aplicacion.esquemas import (
    AccountRead,
    AuthUserRead,
    DriverAssignmentRead,
    DriverShiftEntryRead,
    DriverShiftCloseCreate,
    DriverPaymentCreate,
    DriverQrValidateCreate,
    DriverShiftRead,
    FareRead,
    HealthRead,
    LoginCreate,
    LoginRead,
    PaymentCreate,
    PaymentHistoryRead,
    PaymentReceipt,
    PassengerRegistrationCreate,
    QrCreate,
    QrRead,
    RouteRead,
    ShiftCloseRead,
    TopUpCreate,
    TopUpReceipt,
    TransferCreate,
    TransferRead,
    TripRead,
)
from aplicacion.modelos import Driver, Role, Trip, User, UserRole
from aplicacion.servicios import (
    active_driver_shift,
    assigned_driver_shift,
    close_driver_shift,
    create_payment,
    create_qr,
    create_top_up,
    create_transfer,
    driver_shift_history,
    driver_shift_summary,
    DriverShiftSummary,
    get_current_fare,
    get_trip,
    list_payments,
    list_routes,
    list_trips,
    qr_image_data_uri,
    record_driver_payment,
    redeem_qr,
)
from aplicacion.contrasenas import hash_password


# Las rutas son la recepción de la API: traducen lo que llega y delegan las
# decisiones de negocio en servicios.py para que no haya reglas distintas por endpoint.
SessionDependency = Annotated[Session, Depends(get_session)]
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1")
demo_router = APIRouter(prefix="/demo/account", tags=["Demostración"])
auth_router = APIRouter(prefix="/auth", tags=["Autenticación"])
driver_router = APIRouter(prefix="/driver", tags=["Conductor"])


@router.get("/health", response_model=HealthRead, tags=["Sistema"])
def health() -> HealthRead:
    return HealthRead(status="ok", service="qrpass-api", mode="demo")


@router.get("/ready", response_model=HealthRead, tags=["Sistema"], summary="Verificar disponibilidad de la base de datos")
def readiness(request: Request) -> HealthRead:
    try:
        with request.app.state.database.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        logger.error("La comprobación de disponibilidad de la base de datos falló.", exc_info=error)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La base de datos no está disponible.",
        ) from error
    return HealthRead(status="ready", service="qrpass-api", mode="demo")


@router.get("/routes", response_model=list[RouteRead], tags=["Rutas"])
def routes(session: SessionDependency) -> list[RouteRead]:
    return [RouteRead.model_validate(route) for route in list_routes(session)]


@router.get("/fares/current", response_model=list[FareRead], tags=["Tarifas"])
def current_fares(
    session: SessionDependency,
    route_id: Annotated[int | None, Query(gt=0)] = None,
    on_date: date | None = None,
) -> list[FareRead]:
    return [FareRead.model_validate(fare) for fare in get_current_fare(session, route_id, on_date)]


def _auth_user_read(user: User) -> AuthUserRead:
    if user.username is None:
        raise HTTPException(status_code=409, detail="La cuenta no tiene un usuario de inicio de sesión.")
    return AuthUserRead(
        user_id=user.id,
        username=user.username,
        email=user.email,
        names=user.names,
        roles=sorted(user_role.role.code for user_role in user.roles),
    )


@auth_router.post(
    "/register",
    response_model=AuthUserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una cuenta pasajera",
)
def register_passenger(payload: PassengerRegistrationCreate, session: SessionDependency) -> AuthUserRead:
    email = str(payload.email).strip().lower()
    if session.scalar(select(User.id).where(User.email == email)) is not None:
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese correo.")
    passenger_role = session.scalar(select(Role).where(Role.code == "PASSENGER"))
    if passenger_role is None:
        raise HTTPException(status_code=503, detail="Los roles del sistema no están inicializados.")
    user = User(
        names=" ".join(payload.names.split()),
        username=email,
        email=email,
        password_hash=hash_password(payload.password),
        privacy_consent_at=datetime.datetime.now(datetime.timezone.utc),
        document_number=f"QRPASS-{secrets.token_hex(12)}",
        wallet_balance=0,
        status="active",
    )
    session.add(user)
    session.flush()
    # Una cuenta recién llegada empieza como pasajera; el registro público no
    # puede conceder por accidente permisos de conductor.
    user.roles.append(UserRole(role=passenger_role))
    session.commit()
    session.refresh(user)
    return _auth_user_read(user)


@auth_router.post("/login", response_model=LoginRead, summary="Iniciar sesión")
def login(payload: LoginCreate, request: Request, session: SessionDependency) -> LoginRead:
    user = session.execute(
        select(User)
        .options(joinedload(User.roles).joinedload(UserRole.role))
        .where(User.username == payload.username, User.status == "active")
    ).unique().scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(user.id, request.app.state.auth_secret)
    return LoginRead(
        access_token=token,
        expires_in=ACCESS_TOKEN_SECONDS,
        user=_auth_user_read(user),
    )


@auth_router.get("/me", response_model=AuthUserRead, summary="Consultar usuario y roles autenticados")
def current_user(user: AuthenticatedUser) -> AuthUserRead:
    return _auth_user_read(user)


@driver_router.get(
    "/demo/assignment",
    response_model=DriverAssignmentRead,
    summary="Consultar asignación de conductor de demostración",
)
def driver_assignment(
    user: Annotated[User, Depends(require_role("DRIVER"))],
    session: SessionDependency,
) -> DriverAssignmentRead:
    shift = assigned_driver_shift(session, user)
    driver = session.get(Driver, user.id)
    if shift is None or driver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La cuenta no tiene una asignación de demostración disponible.",
        )
    return DriverAssignmentRead(
        driver_name=user.names,
        license_number=driver.license_number,
        route_id=shift.route_id,
        route_name=shift.route.name,
        vehicle_plate=shift.vehicle.plate,
        shift_status=shift.status,
    )


def _driver_shift_dto(summary: DriverShiftSummary) -> DriverShiftRead:
    shift = summary["shift"]
    return DriverShiftRead(
        shift_id=shift.id,
        route_id=shift.route_id,
        route_name=shift.route.name,
        vehicle_plate=shift.vehicle.plate,
        status=shift.status,
        starts_at=shift.starts_at,
        ends_at=shift.ends_at,
        cash_total=summary["cash"],
        qr_total=summary["qr"],
        card_total=summary["card"],
        payment_count=summary["payment_count"],
        cash_counted=shift.cash_counted,
        cash_difference=shift.cash_difference,
        entries=[
            DriverShiftEntryRead(
                payment_id=entry["payment_id"],
                route_name=entry["route_name"],
                method=entry["method"],
                amount=entry["amount"],
                created_at=entry["created_at"],
            )
            for entry in summary["entries"]
        ],
    )


def _trip_read(trip: Trip) -> TripRead:
    return TripRead(
        trip_id=trip.id,
        route_id=trip.route_id,
        route_name=trip.route.name,
        payment_id=trip.payment_id,
        method=trip.payment.method,
        movement_type=trip.payment.movement_type,
        amount=trip.payment.amount,
        status=trip.payment.status,
        created_at=trip.created_at,
        transferred_to=trip.origin_transfer.destination_route.name if trip.origin_transfer else None,
    )


@driver_router.get("/shift", response_model=DriverShiftRead, summary="Consultar recaudo del turno activo")
def current_driver_shift(
    user: Annotated[User, Depends(require_role("DRIVER"))],
    session: SessionDependency,
) -> DriverShiftRead:
    summary = driver_shift_summary(session, user)
    if summary is None:
        raise HTTPException(status_code=404, detail="No hay un turno activo asignado.")
    return _driver_shift_dto(summary)


@driver_router.get(
    "/shifts/history",
    response_model=list[DriverShiftRead],
    summary="Consultar los cierres de turno recientes",
)
def recent_driver_shifts(
    user: Annotated[User, Depends(require_role("DRIVER"))],
    session: SessionDependency,
) -> list[DriverShiftRead]:
    return [_driver_shift_dto(summary) for summary in driver_shift_history(session, user)]


@driver_router.post("/shift/start", response_model=DriverShiftRead, summary="Iniciar el turno asignado")
def start_driver_shift(
    route_id: Annotated[int, Query(gt=0)],
    user: Annotated[User, Depends(require_role("DRIVER"))],
    session: SessionDependency,
) -> DriverShiftRead:
    shift = active_driver_shift(session, user)
    if shift is not None:
        if shift.route_id != route_id:
            raise HTTPException(status_code=403, detail="Solo puedes iniciar la ruta asignada.")
        summary = driver_shift_summary(session, user)
        if summary is None:
            raise HTTPException(status_code=409, detail="No se pudo consultar el turno activo.")
        return _driver_shift_dto(summary)
    shift = assigned_driver_shift(session, user)
    if shift is None:
        raise HTTPException(status_code=409, detail="No hay una asignación para iniciar.")
    if shift.route_id != route_id:
        raise HTTPException(status_code=403, detail="Solo puedes iniciar la ruta asignada.")
    shift.status = "active"
    shift.starts_at = datetime.datetime.now(datetime.timezone.utc)
    session.commit()
    summary = driver_shift_summary(session, user)
    if summary is None:
        raise HTTPException(status_code=409, detail="No se pudo iniciar el turno asignado.")
    return _driver_shift_dto(summary)


@driver_router.post("/shift/payments", response_model=PaymentReceipt, status_code=status.HTTP_201_CREATED)
def driver_record_payment(
    payload: DriverPaymentCreate,
    user: Annotated[User, Depends(require_role("DRIVER"))],
    session: SessionDependency,
) -> PaymentReceipt:
    payment, trip, balance = record_driver_payment(
        session, user, payload.method, payload.card_type.value if payload.card_type else None,
        payload.idempotency_key,
    )
    return PaymentReceipt(
        payment_id=payment.id, trip_id=trip.id, route_id=trip.route_id,
        route_name=trip.route.name, method=payment.method, card_type=payload.card_type.value if payload.card_type else None,
        movement_type=payment.movement_type, amount=payment.amount, wallet_balance=balance,
        status=payment.status, created_at=payment.created_at,
    )


@driver_router.post("/shift/close", response_model=ShiftCloseRead, summary="Cerrar y consolidar un turno")
def close_shift(
    payload: DriverShiftCloseCreate,
    user: Annotated[User, Depends(require_role("DRIVER"))],
    session: SessionDependency,
) -> ShiftCloseRead:
    summary = close_driver_shift(session, user, payload.cash_counted)
    return ShiftCloseRead(shift=_driver_shift_dto(summary), closed=True)


@driver_router.post("/qr/validate", response_model=PaymentReceipt, status_code=status.HTTP_201_CREATED)
def validate_passenger_qr(
    payload: DriverQrValidateCreate,
    request: Request,
    user: Annotated[User, Depends(require_role("DRIVER"))],
    session: SessionDependency,
) -> PaymentReceipt:
    payment, trip, balance = redeem_qr(
        session, user, payload.token, request.app.state.auth_secret, payload.idempotency_key,
    )
    return PaymentReceipt(
        payment_id=payment.id, trip_id=trip.id, route_id=trip.route_id,
        route_name=trip.route.name, method=payment.method, movement_type=payment.movement_type,
        amount=payment.amount, wallet_balance=balance, status=payment.status,
        created_at=payment.created_at,
    )


@demo_router.get("", response_model=AccountRead, summary="Consultar la cuenta autenticada")
def demo_account(user: AuthenticatedUser) -> AccountRead:
    return AccountRead(user_id=user.id, names=user.names, wallet_balance=user.wallet_balance)


@demo_router.post("/qr", response_model=QrRead, status_code=status.HTTP_201_CREATED)
def generate_demo_qr(
    payload: QrCreate,
    request: Request,
    user: AuthenticatedUser,
    session: SessionDependency,
) -> QrRead:
    qr_code = create_qr(
        session, user, payload.route_id, payload.validity_minutes, request.app.state.auth_secret,
    )
    return QrRead(
        qr_id=qr_code.id,
        token=qr_code.token,
        status=qr_code.status,
        created_at=qr_code.created_at,
        expires_at=qr_code.expires_at,
        image_data_uri=qr_image_data_uri(qr_code.token),
    )


@router.get("/payments/history", response_model=list[PaymentHistoryRead], tags=["Pagos"], summary="Consultar el historial unificado de pagos")
def payment_history(user: AuthenticatedUser, session: SessionDependency) -> list[PaymentHistoryRead]:
    return [
        PaymentHistoryRead(
            payment_id=payment.id,
            movement_type=payment.movement_type,
            method=payment.method,
            amount=payment.amount,
            balance_before=payment.balance_before,
            balance_after=payment.balance_after,
            status=payment.status,
            created_at=payment.created_at,
            trip_id=payment.trip.id if payment.trip else None,
            route_id=payment.trip.route_id if payment.trip else None,
            route_name=payment.trip.route.name if payment.trip else None,
        )
        for payment in list_payments(session, user)
    ]


@router.get("/trips", response_model=list[TripRead], tags=["Viajes"], summary="Consultar el historial de viajes")
def trip_history(user: AuthenticatedUser, session: SessionDependency) -> list[TripRead]:
    return [_trip_read(trip) for trip in list_trips(session, user)]


@router.get("/trips/{trip_id}", response_model=TripRead, tags=["Viajes"], summary="Consultar el detalle de un viaje")
def trip_detail(trip_id: int, user: AuthenticatedUser, session: SessionDependency) -> TripRead:
    return _trip_read(get_trip(session, user, trip_id))


@demo_router.get("/trips", response_model=list[TripRead], summary="Consultar el historial de prueba")
def demo_trip_history(user: AuthenticatedUser, session: SessionDependency) -> list[TripRead]:
    return [_trip_read(trip) for trip in list_trips(session, user)]


@demo_router.post("/payments", response_model=PaymentReceipt, status_code=status.HTTP_201_CREATED)
def pay_for_trip(payload: PaymentCreate, user: AuthenticatedUser, session: SessionDependency) -> PaymentReceipt:
    payment, trip, wallet_balance = create_payment(session, user, payload)
    return PaymentReceipt(
        payment_id=payment.id,
        trip_id=trip.id,
        route_id=trip.route_id,
        route_name=trip.route.name,
        method=payment.method,
        card_type=payload.card_type.value if payload.card_type else None,
        movement_type=payment.movement_type,
        amount=payment.amount,
        wallet_balance=wallet_balance,
        status=payment.status,
        created_at=payment.created_at,
    )


@demo_router.post("/top-ups", response_model=TopUpReceipt, status_code=status.HTTP_201_CREATED)
def top_up_wallet(payload: TopUpCreate, user: AuthenticatedUser, session: SessionDependency) -> TopUpReceipt:
    payment = create_top_up(session, user, payload)
    return TopUpReceipt(
        payment_id=payment.id,
        amount=payment.amount,
        wallet_balance=payment.balance_after,
        status=payment.status,
        created_at=payment.created_at,
    )


@demo_router.post("/transfers", response_model=TransferRead, status_code=status.HTTP_201_CREATED)
def transfer_trip(payload: TransferCreate, user: AuthenticatedUser, session: SessionDependency) -> TransferRead:
    transfer = create_transfer(session, user, payload)
    return TransferRead(
        transfer_id=transfer.id,
        origin_trip_id=transfer.origin_trip_id,
        origin_route=transfer.origin_trip.route.name,
        destination_route_id=transfer.destination_route_id,
        destination_route=transfer.destination_route.name,
        created_at=transfer.created_at,
    )


router.include_router(auth_router)
router.include_router(driver_router)
router.include_router(demo_router)
