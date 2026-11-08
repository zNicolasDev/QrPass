from __future__ import annotations

import base64
import hashlib
import hmac
import io
import json
import secrets
from datetime import timedelta

import qrcode
from qrcode.image.svg import SvgPathImage
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import Usuario, Pago, Viaje, CodigoQr, Turno, Ruta, Tarifa
from app.servicios.comun import ErrorDominio, ahora_servicio
from app.servicios.rutas_tarifas import _obtener_ruta_activa, _obtener_tarifa_ruta, _validar_destino_ruta


def _encode_qr_payload(payload: dict[str, object]) -> str:
    serialized = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(serialized).rstrip(b"=").decode("ascii")


def _decode_qr_payload(encoded: str) -> dict[str, object]:
    payload = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
    decoded = json.loads(payload)
    if not isinstance(decoded, dict):
        raise ValueError("QR payload must be an object")
    return decoded


def crear_imagen_qr(token: str) -> str:
    code = qrcode.QRCode(box_size=8, border=4, image_factory=SvgPathImage)
    code.add_data(token)
    code.make(fit=True)
    image = code.make_image(fill_color="#173f31", back_color="#ffffff")
    buffer = io.BytesIO()
    image.save(buffer)
    encoded_image = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded_image}"


def crear_qr_turno_conductor(
    session: Session, driver: Usuario, signing_secret: bytes, renovar: bool = False,
) -> CodigoQr:
    from app.servicios.turnos import obtener_turno_activo_conductor
    shift = obtener_turno_activo_conductor(session, driver)
    if shift is None:
        raise ErrorDominio(409, "Inicia el turno antes de mostrar el QR del bus.")

    now = ahora_servicio()
    current_qr = session.scalar(
        select(CodigoQr)
        .where(
            CodigoQr.usuario_id == driver.id,
            CodigoQr.estado == "active",
            CodigoQr.vence_en > now,
        )
        .order_by(CodigoQr.creado_en.desc())
        .limit(1)
    )
    if current_qr is not None and not renovar:
        try:
            prefix, encoded_payload, _ = current_qr.token.split(".")
            claims = _decode_qr_payload(encoded_payload)
            if (
                prefix == "QRP1"
                and claims.get("kind") == "bus_boarding"
                and claims.get("shift_id") == shift.id
                and claims.get("route_id") == shift.ruta_id
            ):
                return current_qr
        except (ValueError, TypeError, IndexError, json.JSONDecodeError):
            pass

    session.execute(
        update(CodigoQr)
        .where(CodigoQr.usuario_id == driver.id, CodigoQr.estado == "active")
        .values(estado="revoked")
    )
    qr_code = CodigoQr(
        usuario_id=driver.id,
        token=secrets.token_urlsafe(48),
        estado="active",
        creado_en=now,
        vence_en=now + timedelta(minutes=15),
    )
    session.add(qr_code)
    session.flush()
    payload = {
        "v": 1,
        "kind": "bus_boarding",
        "qr_id": qr_code.id,
        "sub": driver.id,
        "route_id": shift.ruta_id,
        "shift_id": shift.id,
        "exp": int(qr_code.vence_en.timestamp()),
        "jti": secrets.token_urlsafe(18),
    }
    encoded_payload = _encode_qr_payload(payload)
    signature = hmac.new(signing_secret, encoded_payload.encode("ascii"), hashlib.sha256).hexdigest()
    qr_code.token = f"QRP1.{encoded_payload}.{signature}"
    session.commit()
    session.refresh(qr_code)
    return qr_code


def validar_qr_de_abordaje(
    session: Session,
    passenger: Usuario,
    token: str,
    signing_secret: bytes,
    idempotency_key: str,
    destination: str | None = None,
) -> tuple[Pago, Viaje, int]:
    try:
        prefix, encoded_payload, signature = token.split(".")
        expected = hmac.new(signing_secret, encoded_payload.encode("ascii"), hashlib.sha256).hexdigest()
        if prefix != "QRP1" or not hmac.compare_digest(signature, expected):
            raise ValueError("Invalid signature")
        payload = _decode_qr_payload(encoded_payload)
        qr_id = payload.get("qr_id")
        driver_id = payload.get("sub")
        route_id = payload.get("route_id")
        shift_id = payload.get("shift_id")
        expires_at = payload.get("exp")
        if payload.get("kind") != "bus_boarding" or not all(
            isinstance(value, int) and not isinstance(value, bool)
            for value in (qr_id, driver_id, route_id, shift_id, expires_at)
        ):
            raise ValueError("Invalid claims")
    except (ValueError, KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
        raise ErrorDominio(422, "El QR del bus no es válido.") from None

    prior = session.scalar(select(Pago).where(
        Pago.usuario_id == passenger.id,
        Pago.clave_idempotencia == idempotency_key,
    ))
    if prior is not None:
        if prior.codigo_qr_id != qr_id or prior.viaje is None:
            raise ErrorDominio(409, "La clave de idempotencia ya se usó para otra operación.")
        if prior.viaje.tarifa.destino != destination:
            raise ErrorDominio(409, "La clave de idempotencia ya se usó para otro destino.")
        return prior, prior.viaje, prior.saldo_posterior

    prior_boarding = session.scalar(select(Pago).where(
        Pago.usuario_id == passenger.id,
        Pago.codigo_qr_id == qr_id,
        Pago.tipo_movimiento == "fare_payment",
    ))
    if prior_boarding is not None:
        raise ErrorDominio(409, "Este abordaje ya fue pagado con el QR actual del bus.")

    now = ahora_servicio()
    if expires_at <= int(now.timestamp()):
        raise ErrorDominio(410, "El QR del bus expiró. Pide que lo actualicen en la pantalla del bus.")
    qr_code = session.scalar(select(CodigoQr).where(
        CodigoQr.id == qr_id,
        CodigoQr.usuario_id == driver_id,
        CodigoQr.token == token,
        CodigoQr.estado == "active",
        CodigoQr.vence_en > now,
    ))
    shift = session.scalar(select(Turno).where(
        Turno.id == shift_id,
        Turno.conductor_id == driver_id,
        Turno.estado == "active",
        Turno.ruta_id == route_id,
    ))
    driver = session.get(Usuario, driver_id)
    if qr_code is None or shift is None or driver is None or driver.estado != "active":
        raise ErrorDominio(409, "El QR ya no corresponde a un turno activo del bus.")

    _obtener_ruta_activa(session, route_id)
    # La ruta 48 exige destino y cada destino tiene su propio valor.
    _validar_destino_ruta(session, route_id, destination)
    fare = _obtener_tarifa_ruta(session, route_id, destination)
    balance_before = passenger.saldo_billetera
    balance_after = session.scalar(
        update(Usuario)
        .where(Usuario.id == passenger.id, Usuario.estado == "active", Usuario.saldo_billetera >= fare.monto)
        .values(saldo_billetera=Usuario.saldo_billetera - fare.monto)
        .returning(Usuario.saldo_billetera)
    )
    if balance_after is None:
        session.rollback()
        raise ErrorDominio(409, "Saldo insuficiente para pagar el viaje.")
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
    session.commit()
    session.refresh(payment)
    session.refresh(trip)
    return payment, trip, balance_after
