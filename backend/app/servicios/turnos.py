from __future__ import annotations

from typing import Any
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload

from app.dtos import MedioPago
from app.models import Usuario, Turno, Pago, Viaje, Ruta, Tarifa, Conductor, EmpresaTransporte, Vehiculo
from app.servicios.comun import ErrorDominio, ahora_servicio, ResumenTurnoConductor, ResumenMovimientoTurno
from app.servicios.rutas_tarifas import _obtener_tarifa_ruta, _obtener_ruta_activa


def obtener_asignaciones_conductor(session: Session, driver: Usuario) -> list[Turno]:
    return list(
        session.scalars(
            select(Turno)
            .options(joinedload(Turno.ruta), joinedload(Turno.vehiculo))
            .where(
                Turno.conductor_id == driver.id,
                Turno.finaliza_en.is_(None),
                Turno.estado.in_(("assigned", "active")),
            )
            .order_by(Turno.inicia_en.desc(), Turno.id.desc())
        )
    )


def _asegurar_asignacion_ruta(session: Session, driver: Usuario, route_id: int) -> Turno | None:
    """Garantiza una asignación para la ruta indicada.

    Si ya existe una asignación para esa ruta, la devuelve. Si no, la recrea
    a partir del último turno cerrado de esa misma ruta, para que el conductor
    pueda volver a iniciar sin depender de un administrador.
    """
    shift = session.scalar(
        select(Turno)
        .options(joinedload(Turno.ruta), joinedload(Turno.vehiculo))
        .where(
            Turno.conductor_id == driver.id,
            Turno.ruta_id == route_id,
            Turno.finaliza_en.is_(None),
            Turno.estado.in_(("assigned", "active")),
        )
        .order_by(Turno.inicia_en.desc(), Turno.id.desc())
    )
    if shift is not None:
        return shift
    last_closed = session.scalar(
        select(Turno).where(
            Turno.conductor_id == driver.id,
            Turno.ruta_id == route_id,
            Turno.estado == "closed",
        ).order_by(Turno.finaliza_en.desc(), Turno.id.desc())
    )
    if last_closed is None:
        return None
    session.add(Turno(
        conductor_id=driver.id,
        vehiculo_id=last_closed.vehiculo_id,
        ruta_id=route_id,
        inicia_en=ahora_servicio(),
        estado="assigned",
    ))
    session.commit()
    return session.scalar(
        select(Turno)
        .options(joinedload(Turno.ruta), joinedload(Turno.vehiculo))
        .where(
            Turno.conductor_id == driver.id,
            Turno.ruta_id == route_id,
            Turno.finaliza_en.is_(None),
            Turno.estado.in_(("assigned", "active")),
        )
        .order_by(Turno.inicia_en.desc(), Turno.id.desc())
    )

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


def _asegurar_asignacion_conductor(session: Session, driver: Usuario) -> Turno | None:
    """Garantiza que el conductor conserve su ruta y vehículo después de cerrar un turno.

    Si no tiene un turno asignado/activo, se crea uno nuevo "assigned" copiando la
    ruta y el vehículo del último turno cerrado. Así puede volver a iniciar turno
    sin tener que restablecer los datos de la cuenta.
    """
    assignment = obtener_asignacion_conductor(session, driver)
    if assignment is not None:
        return assignment
    last_closed = session.scalar(
        select(Turno)
        .where(Turno.conductor_id == driver.id, Turno.estado == "closed")
        .order_by(Turno.finaliza_en.desc(), Turno.id.desc())
    )
    if last_closed is None:
        return None
    session.add(Turno(
        conductor_id=driver.id,
        vehiculo_id=last_closed.vehiculo_id,
        ruta_id=last_closed.ruta_id,
        inicia_en=ahora_servicio(),
        estado="assigned",
    ))
    session.commit()
    return obtener_asignacion_conductor(session, driver)


def asignar_turno_conductor(
    session: Session,
    driver: Usuario,
    route_id: int,
    plate: str,
    company_name: str = "QrPass",
) -> Turno:
    # Provisionamiento operativo: deja al conductor con un turno asignado que
    # todavía no está activo. La ruta debe existir en el catálogo importado.
    if session.get(Conductor, driver.id) is None:
        raise ErrorDominio(409, "La cuenta no tiene perfil de conductor.")
    route = _obtener_ruta_activa(session, route_id)

    company = session.scalar(select(EmpresaTransporte).where(EmpresaTransporte.nombre == company_name))
    if company is None:
        company = EmpresaTransporte(nombre=company_name)
        session.add(company)
        session.flush()

    normalized_plate = plate.strip().upper()
    vehicle = session.scalar(select(Vehiculo).where(Vehiculo.placa == normalized_plate))
    if vehicle is None:
        vehicle = Vehiculo(empresa_id=company.id, placa=normalized_plate)
        session.add(vehicle)
        session.flush()

    existing = session.scalar(
        select(Turno).where(
            Turno.conductor_id == driver.id,
            Turno.ruta_id == route.id,
            Turno.finaliza_en.is_(None),
            Turno.estado.in_(("assigned", "active")),
        )
    )
    if existing is not None:
        return existing

    shift = Turno(
        conductor_id=driver.id,
        vehiculo_id=vehicle.id,
        ruta_id=route.id,
        inicia_en=ahora_servicio(),
        estado="assigned",
    )
    session.add(shift)
    session.commit()
    session.refresh(shift)
    return shift


def iniciar_turno_conductor(session: Session, driver: Usuario, route_id: int) -> ResumenTurnoConductor:
    shift = obtener_turno_activo_conductor(session, driver)
    if shift is not None:
        if shift.ruta_id != route_id:
            raise ErrorDominio(403, "Solo puedes iniciar la ruta asignada.")
        summary = resumir_turno_conductor(session, driver)
        if summary is None:
            raise ErrorDominio(409, "No se pudo consultar el turno activo.")
        return summary

    shift = _asegurar_asignacion_ruta(session, driver, route_id)
    if shift is None:
        raise ErrorDominio(409, "No hay una asignación para esa ruta.")
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
        estado="completed",
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
    # El conductor conserva su ruta y vehículo para poder iniciar un nuevo turno.
    _asegurar_asignacion_conductor(session, driver)
    # Prepara la siguiente asignación para que el conductor pueda iniciar
    # un nuevo turno sin depender de la CLI ni de un administrador.
    try:
        asignar_turno_conductor(session, driver, shift.ruta_id, shift.vehiculo.placa)
    except Exception:
        pass
    return summary
