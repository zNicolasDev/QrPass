from __future__ import annotations

from typing import Any
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload

from app.dtos import MedioPago
from app.models import Usuario, Turno, Pago, Viaje, Ruta, Tarifa, Conductor
from app.servicios.comun import ErrorDominio, ahora_servicio, ResumenTurnoConductor, ResumenMovimientoTurno
from app.servicios.rutas_tarifas import _obtener_tarifa_ruta


def obtener_turno_activo_conductor(session: Session, driver: Usuario) -> Turno | None:
    return session.scalar(
        select(Turno)
        .options(joinedload(Turno.ruta), joinedload(Turno.vehiculo))
        .where(Turno.conductor_id == driver.id, Turno.estado == "active", Turno.finaliza_en.is_(None))
        .order_by(Turno.inicia_en.desc(), Turno.id.desc())
    )


def obtener_asignacion_conductor(session: Session, driver: Usuario) -> Turno | None:
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


def registrar_pago_conductor(
    session: Session,
    driver: Usuario,
    method: MedioPago,
    card_type: str | None,
    idempotency_key: str,
) -> tuple[Pago, Viaje, int]:
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
    shift = obtener_turno_activo_conductor(session, driver)
    return _resumir_turno(session, shift) if shift is not None else None


def consultar_historial_turnos(session: Session, driver: Usuario, limit: int = 20) -> list[ResumenTurnoConductor]:
    shifts = session.scalars(
        select(Turno)
        .options(joinedload(Turno.ruta), joinedload(Turno.vehiculo))
        .where(Turno.conductor_id == driver.id, Turno.estado == "closed")
        .order_by(Turno.finaliza_en.desc(), Turno.id.desc())
        .limit(limit)
    )
    return [_resumir_turno(session, shift) for shift in shifts]


def cerrar_turno_conductor(session: Session, driver: Usuario, cash_counted: int) -> ResumenTurnoConductor:
    summary = resumir_turno_conductor(session, driver)
    if summary is None:
        raise ErrorDominio(409, "No hay un turno activo para cerrar.")
    shift = summary["shift"]
    if not isinstance(shift, Turno):
        raise RuntimeError("La consulta de turno devolvió un tipo inesperado.")
    shift.finaliza_en = ahora_servicio()
    shift.estado = "closed"
    shift.efectivo_contado = cash_counted
    shift.diferencia_efectivo = cash_counted - int(summary["cash"])
    session.commit()
    session.refresh(shift)
    return summary