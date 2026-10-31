from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.dtos import CrearPagoSolicitud, MedioPago, CrearRecargaSolicitud
from app.models import Usuario, Pago, Viaje, Ruta, Tarifa
from app.servicios.comun import ErrorDominio, ahora_servicio
from app.servicios.rutas_tarifas import _obtener_ruta_activa, _validar_destino_ruta, _obtener_tarifa_ruta


def crear_pago(session: Session, user: Usuario, request: CrearPagoSolicitud) -> tuple[Pago, Viaje, int]:
    if request.medio == MedioPago.WALLET:
        raise ErrorDominio(422, "Para pagar con saldo, escanea el QR que muestra el bus.")

    if request.clave_idempotencia:
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
            if prior.viaje.tarifa.destino != request.destino:
                raise ErrorDominio(409, "La clave de idempotencia ya se usó para otro destino.")
            return prior, prior.viaje, prior.saldo_posterior
    route = _obtener_ruta_activa(session, request.ruta_id)
    _validar_destino_ruta(session, route.id, request.destino)
    fare = _obtener_tarifa_ruta(session, route.id, request.destino)
    now = ahora_servicio()
    balance_before = user.saldo_billetera
    balance_after = balance_before

    if request.medio == MedioPago.CASH:
        payment_method = "cash"
    else:
        if request.tipo_tarjeta is None:
            raise ErrorDominio(422, "El método tarjeta requiere indicar débito o crédito.")
        payment_method = f"card_{request.tipo_tarjeta.value}"

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
    session.commit()
    session.refresh(payment)
    session.refresh(trip)
    return payment, trip, balance_after


def crear_recarga(session: Session, user: Usuario, request: CrearRecargaSolicitud) -> Pago:
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