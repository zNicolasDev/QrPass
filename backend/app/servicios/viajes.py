from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Usuario, Viaje, Pago, Transbordo
from app.servicios.comun import ErrorDominio


def listar_viajes(session: Session, user: Usuario) -> list[Viaje]:
    statement = (
        select(Viaje)
        .join(Viaje.pago)
        .options(joinedload(Viaje.ruta), joinedload(Viaje.pago), joinedload(Viaje.transbordo_origen).joinedload(Transbordo.ruta_destino))
        .where(Pago.usuario_id == user.id)
        .order_by(Viaje.creado_en.desc(), Viaje.id.desc())
    )
    return list(session.scalars(statement))


def obtener_viaje(session: Session, user: Usuario, trip_id: int) -> Viaje:
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
    statement = (
        select(Pago)
        .options(joinedload(Pago.viaje).joinedload(Viaje.ruta))
        .where(Pago.usuario_id == user.id)
        .order_by(Pago.creado_en.desc(), Pago.id.desc())
    )
    return list(session.scalars(statement))