from __future__ import annotations
# Este módulo contiene las reglas de negocio de pagos, tarifas, QR, traspasos y turnos.

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
from sqlalchemy.orm import Session, joinedload, selectinload

from app.dtos import CrearPagoSolicitud, MedioPago, CrearRecargaSolicitud, CrearTransbordoSolicitud
from app.models import Tarifa, Pago, CodigoQr, Ruta, Turno, Transbordo, Viaje, Usuario
from app.models import Rol, RolUsuario, Conductor
from app.passwords import crear_hash_contrasena
from app.passwords import verificar_contrasena


# Aquí están las decisiones que una persona esperaría que siempre se cumplan,
# use la pantalla actual o un cliente futuro distinto.
IBAGUE_TIMEZONE = ZoneInfo("America/Bogota")


# Estructuras internas para pasar un resumen claro del servicio al controlador.
class ResumenMovimientoTurno(TypedDict):
    payment_id: int
    route_name: str
    method: str
    amount: int
    created_at: datetime


class ResumenTurnoConductor(TypedDict):
    shift: Turno
    cash: int
    qr: int
    card: int
    payment_count: int
    entries: list[ResumenMovimientoTurno]


class ErrorDominio(Exception):
    # El servicio informa una regla incumplida sin importar cómo se presenta
    # el resultado (API, pruebas u otra interfaz).
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


# Registra una cuenta pasajera y asigna únicamente el rol público permitido.
def registrar_pasajero(session: Session, names: str, email: str, password: str) -> Usuario:
    normalized_email = email.strip().lower()
    if session.scalar(select(Usuario.id).where(Usuario.correo == normalized_email)) is not None:
        raise ErrorDominio(409, "Ya existe una cuenta con ese correo.")
    passenger_role = session.scalar(select(Rol).where(Rol.codigo == "PASSENGER"))
    if passenger_role is None:
        raise ErrorDominio(503, "Los roles del sistema no están inicializados.")
    user = Usuario(
        nombres=" ".join(names.split()),
        nombre_usuario=normalized_email,
        correo=normalized_email,
        hash_contrasena=crear_hash_contrasena(password),
        consentimiento_privacidad_en=ahora_servicio(),
        numero_documento=f"QRPASS-{secrets.token_hex(12)}",
        saldo_billetera=0,
        estado="active",
    )
    session.add(user)
    session.flush()
    user.roles.append(RolUsuario(rol=passenger_role))
    session.commit()
    session.refresh(user)
    return user


# Busca una cuenta activa y valida su contraseña para iniciar sesión.
def autenticar_usuario(session: Session, username: str, password: str) -> Usuario:
    user = session.execute(
        select(Usuario)
        .options(joinedload(Usuario.roles).joinedload(RolUsuario.rol))
        .where(Usuario.nombre_usuario == username, Usuario.estado == "active")
    ).unique().scalar_one_or_none()
    if user is None or not verificar_contrasena(password, user.hash_contrasena):
        raise ErrorDominio(401, "Usuario o contraseña incorrectos.")
    return user


# Busca una cuenta activa y carga sus roles para validar permisos de la API.
def obtener_usuario_activo(session: Session, user_id: int) -> Usuario | None:
    return session.scalar(
        select(Usuario)
        .options(selectinload(Usuario.roles).selectinload(RolUsuario.rol))
        .where(Usuario.id == user_id, Usuario.estado == "active")
    )


# Comprueba si la cuenta tiene asignado el rol que pide una operación.
def usuario_tiene_rol(user: Usuario, role_code: str) -> bool:
    return any(user_role.rol.codigo == role_code for user_role in user.roles)


# Obtiene el perfil del conductor y su asignación para presentar la respuesta.
def obtener_datos_asignacion_conductor(session: Session, user: Usuario) -> tuple[Conductor | None, Turno | None]:
    # Se consultan el perfil y el turno juntos porque la pantalla necesita ambos.
    return session.get(Conductor, user.id), obtener_asignacion_conductor(session, user)


def ahora_servicio() -> datetime:
    # Todos los vencimientos y registros se comparan con una hora UTC común.
    return datetime.now(timezone.utc)


def fecha_servicio() -> date:
    # Las tarifas se calculan con la fecha local de Ibagué, aunque el servidor
    # esté desplegado en otra zona horaria.
    return datetime.now(IBAGUE_TIMEZONE).date()


# Clasifica una fecha usando el calendario colombiano para elegir la tarifa.
def tipo_dia(day: date) -> str:
    # El día del servicio se entiende según Ibagué; no según la zona horaria
    # del servidor o del celular que hizo la solicitud.
    return "weekend" if day.weekday() == 6 or day in holidays.country_holidays("CO", years=day.year) else "weekday"


def obtener_usuario_demo(session: Session) -> Usuario:
    # Recupera la cuenta fija usada por los flujos de demostración.
    user = session.get(Usuario, 1)
    if user is None or user.estado != "active":
        raise ErrorDominio(404, "La cuenta de demostración no existe o está inactiva.")
    return user


def listar_rutas(session: Session) -> list[Ruta]:
    # Las rutas inactivas no deben aparecer en el catálogo seleccionable.
    statement = select(Ruta).where(Ruta.activa.is_(True)).order_by(Ruta.id)
    return list(session.scalars(statement))


# Busca y devuelve las tarifas activas de una ruta o de todo el catálogo.
def obtener_tarifa_vigente(session: Session, route_id: int | None, on_date: date | None = None) -> list[dict[str, object]]:
    requested_date = on_date or fecha_servicio()
    day_type = tipo_dia(requested_date)
    statement = (
        select(Tarifa)
        .options(joinedload(Tarifa.ruta))
        .join(Tarifa.ruta)
        .where(Tarifa.activa.is_(True), Ruta.activa.is_(True), Tarifa.tipo_dia == day_type)
        .order_by(Ruta.id)
    )
    if route_id is not None:
        statement = statement.where(Tarifa.ruta_id == route_id)

    fares = list(session.scalars(statement))
    if route_id is not None and not fares:
        raise ErrorDominio(404, "No se encontró una tarifa activa para la ruta indicada.")
    return [
        {
            "route_id": fare.ruta_id,
            "route_name": fare.ruta.nombre,
            "day_type": fare.tipo_dia,
            "amount": fare.monto,
            'fecha_servicio': requested_date,
        }
        for fare in fares
    ]


def _encode_qr_payload(payload: dict[str, object]) -> str:
    # Convierte los datos del QR a texto compacto que se puede firmar y compartir.
    serialized = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(serialized).rstrip(b"=").decode("ascii")


def _decode_qr_payload(encoded: str) -> dict[str, object]:
    # Deshace la codificación y rechaza el contenido si no es un objeto JSON.
    payload = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
    decoded = json.loads(payload)
    if not isinstance(decoded, dict):
        raise ValueError("QR payload must be an object")
    return decoded


def crear_imagen_qr(token: str) -> str:
    # Genera una imagen SVG incrustada como data URI; así la API devuelve el QR
    # junto con el token sin guardar un archivo de imagen en el proyecto.
    code = qrcode.QRCode(box_size=8, border=4, image_factory=SvgPathImage)
    code.add_data(token)
    code.make(fit=True)
    image = code.make_image(fill_color="#173f31", back_color="#ffffff")
    buffer = io.BytesIO()
    image.save(buffer)
    encoded_image = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded_image}"


# Revisa ruta, tarifa y saldo; luego guarda y firma un QR temporal.
def crear_codigo_qr(
    session: Session,
    user: Usuario,
    route_id: int,
    validity_minutes: int,
    signing_secret: bytes,
) -> CodigoQr:
    # Antes de emitir el QR se confirma que la ruta exista y que el saldo cubra
    # al menos una tarifa. El QR no debita el saldo todavía.
    route = _obtener_ruta_activa(session, route_id)
    fare = _obtener_tarifa_ruta(session, route.id)
    if user.saldo_billetera < fare.monto:
        raise ErrorDominio(409, "Saldo insuficiente para generar un código de viaje.")
    now = ahora_servicio()
    # Solo se permite un QR activo por cuenta: se revocan los anteriores.
    session.execute(
        update(CodigoQr)
        .where(CodigoQr.usuario_id == user.id, CodigoQr.estado == "active")
        .values(estado="revoked")
    )
    qr_code = CodigoQr(
        usuario_id=user.id,
        token=secrets.token_urlsafe(48),
        estado="active",
        creado_en=now,
        vence_en=now + timedelta(minutes=validity_minutes),
    )
    session.add(qr_code)
    session.flush()
    # El token lleva identificadores y vencimiento; la firma permite detectar
    # cambios hechos al contenido después de generar el QR.
    payload = {
        "v": 1,
        "qr_id": qr_code.id,
        "sub": user.id,
        "route_id": route.id,
        "exp": int(qr_code.vence_en.timestamp()),
        "jti": secrets.token_urlsafe(18),
    }
    encoded_payload = _encode_qr_payload(payload)
    signature = hmac.new(signing_secret, encoded_payload.encode("ascii"), hashlib.sha256).hexdigest()
    qr_code.token = f"QRP1.{encoded_payload}.{signature}"
    session.commit()
    session.refresh(qr_code)
    return qr_code


def _obtener_ruta_activa(session: Session, route_id: int) -> Ruta:
    # Esta consulta compartida evita usar una ruta inexistente o desactivada.
    route = session.scalar(select(Ruta).where(Ruta.id == route_id, Ruta.activa.is_(True)))
    if route is None:
        raise ErrorDominio(404, "La ruta solicitada no existe o está inactiva.")
    return route


def _obtener_tarifa_ruta(session: Session, route_id: int) -> Tarifa:
    # La tarifa se determina con la fecha y zona horaria del servicio, no con
    # la hora local que envíe el navegador.
    day_type = tipo_dia(fecha_servicio())
    fare = session.scalar(select(Tarifa).where(
        Tarifa.ruta_id == route_id,
        Tarifa.tipo_dia == day_type,
        Tarifa.activa.is_(True),
    ))
    if fare is None:
        raise ErrorDominio(404, "La ruta no tiene una tarifa vigente.")
    return fare


# Valida el pago, actualiza el saldo si corresponde y guarda el pago y el viaje.
def crear_pago(session: Session, user: Usuario, request: CrearPagoSolicitud) -> tuple[Pago, Viaje, int]:
    # Flujo general: evitar un cobro duplicado, validar ruta y tarifa, aplicar
    # el medio de pago y guardar juntos el pago y el viaje.
    if request.clave_idempotencia:
        # Si la conexión se corta y la pantalla reintenta, la persona no debe
        # pagar dos veces por haber pulsado una sola vez.
        prior = session.scalar(select(Pago).where(
            Pago.usuario_id == user.id,
            Pago.clave_idempotencia == request.clave_idempotencia,
        ))
        if prior is not None:
            if prior.medio != request.medio.value and prior.medio != (
                f"card_{request.tipo_tarjeta.value}" if request.tipo_tarjeta else request.medio.value
            ):
                raise ErrorDominio(409, "La clave de idempotencia ya se usó para otro pago.")
            if prior.viaje is None:
                raise ErrorDominio(409, "El pago previo no tiene un tiquete asociado.")
            if prior.viaje.ruta_id != request.ruta_id:
                raise ErrorDominio(409, "La clave de idempotencia ya se usó para otra ruta.")
            return prior, prior.viaje, prior.saldo_posterior
    route = _obtener_ruta_activa(session, request.ruta_id)
    fare = _obtener_tarifa_ruta(session, route.id)
    now = ahora_servicio()
    is_wallet_payment = request.medio == MedioPago.WALLET
    balance_before = user.saldo_billetera
    balance_after = balance_before

    if is_wallet_payment:
        # El saldo se descuenta con una condición en la misma operación: dos
        # solicitudes simultáneas no pueden gastar el mismo saldo disponible.
        new_balance = session.scalar(
            update(Usuario)
            .where(Usuario.id == user.id, Usuario.estado == "active", Usuario.saldo_billetera >= fare.monto)
            .values(saldo_billetera=Usuario.saldo_billetera - fare.monto)
            .returning(Usuario.saldo_billetera)
        )
        if new_balance is None:
            session.rollback()
            raise ErrorDominio(409, "Saldo insuficiente para realizar el viaje.")
        balance_after = new_balance
        payment_method = "wallet"
    elif request.medio == MedioPago.CASH:
        payment_method = "cash"
    else:
        if request.tipo_tarjeta is None:
            raise ErrorDominio(422, "El método tarjeta requiere indicar débito o crédito.")
        payment_method = f"card_{request.tipo_tarjeta.value}"

    # Con el saldo resuelto, se construyen los dos registros que forman el pasaje.
    payment = Pago(
        usuario_id=user.id,
        medio=payment_method,
        tipo_movimiento="fare_payment",
        monto=fare.monto,
        clave_idempotencia=request.clave_idempotencia,
        saldo_anterior=balance_before,
        saldo_posterior=balance_after,
        estado="completed_demo",
        creado_en=now,
    )
    session.add(payment)
    session.flush()
    trip = Viaje(
        pago_id=payment.id,
        tarifa_id=fare.id,
        ruta_id=route.id,
        creado_en=now,
    )
    session.add(trip)
    # El pago y el viaje son una sola promesa: o quedan guardados ambos o no
    # queda ninguno, para no mostrar un cobro sin un viaje (ni al revés).
    session.commit()
    session.refresh(payment)
    session.refresh(trip)
    return payment, trip, balance_after


# Acredita saldo una sola vez usando la clave de idempotencia.
def crear_recarga(session: Session, user: Usuario, request: CrearRecargaSolicitud) -> Pago:
    # Una recarga repetida con la misma clave devuelve el pago original y no
    # vuelve a aumentar el saldo.
    prior = session.scalar(select(Pago).where(
        Pago.usuario_id == user.id,
        Pago.clave_idempotencia == request.clave_idempotencia,
    ))
    if prior is not None:
        if prior.tipo_movimiento != "top_up" or prior.monto != request.monto:
            raise ErrorDominio(409, "La clave de idempotencia ya se usó para otra operación.")
        return prior

    now = ahora_servicio()
    balance_after = session.scalar(
        update(Usuario)
        .where(Usuario.id == user.id, Usuario.estado == "active")
        .values(saldo_billetera=Usuario.saldo_billetera + request.monto)
        .returning(Usuario.saldo_billetera)
    )
    if balance_after is None:
        session.rollback()
        raise ErrorDominio(401, "La cuenta no está activa.")
    payment = Pago(
        usuario_id=user.id,
        clave_idempotencia=request.clave_idempotencia,
        medio="wallet",
        tipo_movimiento="top_up",
        monto=request.monto,
        saldo_anterior=balance_after - request.monto,
        saldo_posterior=balance_after,
        estado="completed_demo",
        creado_en=now,
    )
    session.add(payment)
    session.commit()
    session.refresh(payment)
    return payment


def listar_viajes(session: Session, user: Usuario) -> list[Viaje]:
    # El filtro por usuario evita exponer viajes de otras cuentas; las relaciones
    # se cargan para que la respuesta pueda mostrar ruta, pago y transbordo.
    statement = (
        select(Viaje)
        .join(Viaje.pago)
        .options(joinedload(Viaje.ruta), joinedload(Viaje.pago), joinedload(Viaje.transbordo_origen).joinedload(Transbordo.ruta_destino))
        .where(Pago.usuario_id == user.id)
        .order_by(Viaje.creado_en.desc(), Viaje.id.desc())
    )
    return list(session.scalars(statement))


def obtener_viaje(session: Session, user: Usuario, trip_id: int) -> Viaje:
    # Se busca por viaje y dueño al mismo tiempo, para no revelar si otro usuario
    # tiene un identificador de viaje válido.
    trip = session.scalar(
        select(Viaje)
        .join(Viaje.pago)
        .options(
            joinedload(Viaje.ruta),
            joinedload(Viaje.pago),
            joinedload(Viaje.transbordo_origen).joinedload(Transbordo.ruta_destino),
        )
        .where(Viaje.id == trip_id, Pago.usuario_id == user.id)
    )
    if trip is None:
        raise ErrorDominio(404, "No se encontró el viaje solicitado.")
    return trip


def listar_pagos(session: Session, user: Usuario) -> list[Pago]:
    # Devuelve pagos y recargas de la cuenta, ordenados desde el más reciente.
    statement = (
        select(Pago)
        .options(joinedload(Pago.viaje).joinedload(Viaje.ruta))
        .where(Pago.usuario_id == user.id)
        .order_by(Pago.creado_en.desc(), Pago.id.desc())
    )
    return list(session.scalars(statement))


# Valida el viaje anterior y las reglas de tiempo y ruta para hacer el traspaso.
def crear_transbordo(session: Session, user: Usuario, request: CrearTransbordoSolicitud) -> Transbordo:
    # El traspaso no crea otro pago: enlaza el viaje ya pagado con otra ruta
    # y deja intacto el registro que la persona puede consultar después.
    origin_trip = session.scalar(
        select(Viaje)
        .join(Viaje.pago)
        .options(joinedload(Viaje.ruta), joinedload(Viaje.pago))
        .where(Viaje.id == request.viaje_id, Pago.usuario_id == user.id)
    )
    if origin_trip is None:
        raise ErrorDominio(404, "No se encontró el viaje pagado indicado.")
    if origin_trip.pago.tipo_movimiento != "fare_payment":
        raise ErrorDominio(409, "Solo se puede transferir un pago de pasaje.")
    if origin_trip.transbordo_origen is not None:
        raise ErrorDominio(409, "Este viaje ya fue transferido.")
    trip_created_at = origin_trip.creado_en
    if trip_created_at.tzinfo is None:
        trip_created_at = trip_created_at.replace(tzinfo=timezone.utc)
    if ahora_servicio() - trip_created_at > timedelta(minutes=20):
        raise ErrorDominio(409, "El tiempo límite de 20 minutos para el traspaso venció.")

    destination = _obtener_ruta_activa(session, request.ruta_destino_id)
    if destination.id == origin_trip.ruta_id:
        raise ErrorDominio(422, "La ruta de destino debe ser distinta a la ruta original.")
    _obtener_tarifa_ruta(session, destination.id)

    transfer = Transbordo(
        viaje_origen_id=origin_trip.id,
        ruta_destino_id=destination.id,
        creado_en=ahora_servicio(),
    )
    session.add(transfer)
    session.commit()
    session.refresh(transfer)
    return transfer


def obtener_turno_activo_conductor(session: Session, driver: Usuario) -> Turno | None:
    # Un turno activo todavía no tiene hora de finalización.
    return session.scalar(
        select(Turno)
        .options(joinedload(Turno.ruta), joinedload(Turno.vehiculo))
        .where(Turno.conductor_id == driver.id, Turno.estado == "active", Turno.finaliza_en.is_(None))
        .order_by(Turno.inicia_en.desc(), Turno.id.desc())
    )


def obtener_asignacion_conductor(session: Session, driver: Usuario) -> Turno | None:
    # Incluye asignaciones pendientes y activas, pero excluye turnos ya cerrados.
    return session.scalar(
        select(Turno)
        .options(joinedload(Turno.ruta), joinedload(Turno.vehiculo))
        .where(
            Turno.conductor_id == driver.id,
            Turno.estado.in_(("assigned", "active")),
            Turno.finaliza_en.is_(None),
        )
        .order_by(Turno.inicia_en.desc(), Turno.id.desc())
    )


# Inicia la asignación solo si corresponde a la ruta solicitada.
def iniciar_turno_conductor(session: Session, driver: Usuario, route_id: int) -> ResumenTurnoConductor:
    shift = obtener_turno_activo_conductor(session, driver)
    if shift is not None:
        if shift.ruta_id != route_id:
            raise ErrorDominio(403, "Solo puedes iniciar la ruta asignada.")
        summary = resumir_turno_conductor(session, driver)
        if summary is None:
            raise ErrorDominio(409, "No se pudo consultar el turno activo.")
        return summary

    shift = obtener_asignacion_conductor(session, driver)
    if shift is None:
        raise ErrorDominio(409, "No hay una asignación para iniciar.")
    if shift.ruta_id != route_id:
        raise ErrorDominio(403, "Solo puedes iniciar la ruta asignada.")

    shift.estado = "active"
    shift.inicia_en = ahora_servicio()
    session.commit()
    summary = resumir_turno_conductor(session, driver)
    if summary is None:
        raise ErrorDominio(409, "No se pudo iniciar el turno asignado.")
    return summary


def _validar_ruta_conductor(shift: Turno, route_id: int) -> None:
    # El conductor solo puede cobrar en la ruta asociada a su turno actual.
    if shift.ruta_id != route_id:
        raise ErrorDominio(409, "El código o pago no corresponde a la ruta asignada al turno.")


# Verifica turno, firma, vigencia y saldo; consume el QR y registra el viaje.
def validar_y_canjear_qr(
    session: Session,
    driver: Usuario,
    token: str,
    signing_secret: bytes,
    idempotency_key: str,
) -> tuple[Pago, Viaje, int]:
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
        raise ErrorDominio(422, "El código QR no es válido.") from None

    # Un reintento de la misma solicitud devuelve el recibo anterior.
    prior = session.scalar(select(Pago).where(
        Pago.usuario_id == user_id,
        Pago.clave_idempotencia == idempotency_key,
    ))
    if prior is not None:
        if prior.codigo_qr_id != qr_id or prior.viaje is None:
            raise ErrorDominio(409, "La clave de idempotencia ya se usó para otra operación.")
        return prior, prior.viaje, prior.saldo_posterior

    if expires_at <= int(ahora_servicio().timestamp()):
        raise ErrorDominio(410, "El código QR expiró.")
    shift = obtener_turno_activo_conductor(session, driver)
    if shift is None:
        raise ErrorDominio(409, "No hay un turno de conductor activo.")
    _validar_ruta_conductor(shift, route_id)

    qr_code = session.scalar(
        select(CodigoQr).where(
            CodigoQr.id == qr_id,
            CodigoQr.usuario_id == user_id,
            CodigoQr.token == token,
            CodigoQr.estado == "active",
            CodigoQr.vence_en > ahora_servicio(),
        )
    )
    if qr_code is None:
        raise ErrorDominio(409, "El código ya fue usado, revocado o no existe.")
    passenger = session.get(Usuario, user_id)
    if passenger is None or passenger.estado != "active":
        raise ErrorDominio(401, "La cuenta asociada al código no está activa.")

    fare = _obtener_tarifa_ruta(session, route_id)
    now = ahora_servicio()
    balance_before = passenger.saldo_billetera
    # El UPDATE condicional consume el QR una sola vez, incluso si llegan dos
    # validaciones casi al mismo tiempo.
    consumed = session.scalar(
        update(CodigoQr)
        .where(CodigoQr.id == qr_code.id, CodigoQr.estado == "active", CodigoQr.vence_en > now)
        .values(estado="consumed")
        .returning(CodigoQr.id)
        .execution_options(synchronize_session=False)
    )
    if consumed is None:
        session.rollback()
        raise ErrorDominio(409, "El código ya fue utilizado.")
    balance_after = session.scalar(
        update(Usuario)
        .where(Usuario.id == passenger.id, Usuario.estado == "active", Usuario.saldo_billetera >= fare.monto)
        .values(saldo_billetera=Usuario.saldo_billetera - fare.monto)
        .returning(Usuario.saldo_billetera)
    )
    if balance_after is None:
        session.rollback()
        raise ErrorDominio(409, "Saldo insuficiente para validar el código QR.")
    payment = Pago(
        usuario_id=passenger.id,
        codigo_qr_id=qr_code.id,
        clave_idempotencia=idempotency_key,
        medio="wallet",
        tipo_movimiento="fare_payment",
        monto=fare.monto,
        saldo_anterior=balance_before,
        saldo_posterior=balance_after,
        estado="completed_demo",
        creado_en=now,
    )
    session.add(payment)
    session.flush()
    trip = Viaje(
        pago_id=payment.id,
        turno_id=shift.id,
        tarifa_id=fare.id,
        ruta_id=route_id,
        creado_en=now,
    )
    session.add(trip)
    # Consumir QR, descontar saldo y registrar el viaje forman una sola
    # experiencia para el pasajero; un fallo debe dejar el código utilizable.
    session.commit()
    session.refresh(payment)
    session.refresh(trip)
    return payment, trip, balance_after


# Guarda un recaudo manual asociado al turno activo.
def registrar_pago_conductor(
    session: Session,
    driver: Usuario,
    method: MedioPago,
    card_type: str | None,
    idempotency_key: str,
) -> tuple[Pago, Viaje, int]:
    # El recaudo de efectivo/tarjeta se atribuye al turno activo, no a un
    # turno elegido por la interfaz ni a un historial separado del cierre.
    # Se requiere un turno activo antes de registrar cualquier recaudo manual.
    shift = obtener_turno_activo_conductor(session, driver)
    if shift is None:
        raise ErrorDominio(409, "No hay un turno de conductor activo.")
    prior = session.scalar(select(Pago).where(
        Pago.usuario_id == driver.id,
        Pago.clave_idempotencia == idempotency_key,
    ))
    if prior is not None:
        expected_method = f"card_{card_type}" if method == MedioPago.CARD and card_type else method.value
        if (
            prior.viaje is None
            or prior.tipo_movimiento != "fare_payment"
            or prior.medio != expected_method
            or prior.viaje.turno_id != shift.id
        ):
            raise ErrorDominio(409, "La clave de idempotencia ya se usó para otra operación.")
        return prior, prior.viaje, prior.saldo_posterior

    fare = _obtener_tarifa_ruta(session, shift.ruta_id)
    payment_method = f"card_{card_type}" if method == MedioPago.CARD and card_type else method.value
    now = ahora_servicio()
    balance = driver.saldo_billetera
    payment = Pago(
        usuario_id=driver.id,
        clave_idempotencia=idempotency_key,
        medio=payment_method,
        tipo_movimiento="fare_payment",
        monto=fare.monto,
        saldo_anterior=balance,
        saldo_posterior=balance,
        estado="completed_demo",
        creado_en=now,
    )
    session.add(payment)
    session.flush()
    trip = Viaje(
        pago_id=payment.id,
        turno_id=shift.id,
        tarifa_id=fare.id,
        ruta_id=shift.ruta_id,
        creado_en=now,
    )
    session.add(trip)
    session.commit()
    session.refresh(payment)
    session.refresh(trip)
    return payment, trip, balance


def _resumir_turno(session: Session, shift: Turno) -> ResumenTurnoConductor:
    # Una consulta suma los importes por medio; otra obtiene cada movimiento
    # para mostrar el detalle en la pantalla del conductor.
    rows = session.execute(
        select(Pago.medio, func.sum(Pago.monto), func.count(Pago.id))
        .join(Viaje, Viaje.pago_id == Pago.id)
        .where(Viaje.turno_id == shift.id, Pago.tipo_movimiento == "fare_payment")
        .group_by(Pago.medio)
    ).all()
    entries = session.execute(
        select(Pago, Viaje)
        .join(Viaje, Viaje.pago_id == Pago.id)
        .options(joinedload(Viaje.ruta))
        .where(Viaje.turno_id == shift.id, Pago.tipo_movimiento == "fare_payment")
        .order_by(Pago.creado_en.desc(), Pago.id.desc())
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
                "route_name": trip.ruta.nombre,
                "method": payment.medio,
                "amount": payment.monto,
                "created_at": payment.creado_en,
            }
            for payment, trip in entries
        ],
    }


def resumir_turno_conductor(session: Session, driver: Usuario) -> ResumenTurnoConductor | None:
    # Si no hay turno activo no hay recaudo que resumir.
    shift = obtener_turno_activo_conductor(session, driver)
    return _resumir_turno(session, shift) if shift is not None else None


def consultar_historial_turnos(session: Session, driver: Usuario, limit: int = 20) -> list[ResumenTurnoConductor]:
    # Solo se muestran turnos cerrados y se limita la cantidad para mantener
    # la consulta y la respuesta pequeñas.
    shifts = session.scalars(
        select(Turno)
        .options(joinedload(Turno.ruta), joinedload(Turno.vehiculo))
        .where(Turno.conductor_id == driver.id, Turno.estado == "closed")
        .order_by(Turno.finaliza_en.desc(), Turno.id.desc())
        .limit(limit)
    )
    return [_resumir_turno(session, shift) for shift in shifts]


# Cierra el turno y calcula la diferencia del efectivo contado.
def cerrar_turno_conductor(session: Session, driver: Usuario, cash_counted: int) -> ResumenTurnoConductor:
    # Primero se obtiene el recaudo esperado; después se cierra y se guarda el
    # efectivo contado para que ambos valores queden disponibles en el historial.
    summary = resumir_turno_conductor(session, driver)
    if summary is None:
        raise ErrorDominio(409, "No hay un turno activo para cerrar.")
    shift = summary["shift"]
    if not isinstance(shift, Turno):
        raise RuntimeError("La consulta de turno devolvió un tipo inesperado.")
    shift.finaliza_en = ahora_servicio()
    shift.estado = "closed"
    shift.efectivo_contado = cash_counted
    # La diferencia compara lo que el sistema esperaba con lo que el conductor
    # contó; no intenta afirmar que el dinero físico fue verificado.
    shift.diferencia_efectivo = cash_counted - int(summary["cash"])
    session.commit()
    session.refresh(shift)
    return summary
