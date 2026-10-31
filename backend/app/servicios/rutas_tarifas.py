from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Ruta, Tarifa
from app.servicios.comun import ErrorDominio, fecha_servicio, tipo_dia


def listar_rutas(session: Session) -> list[Ruta]:
    statement = select(Ruta).where(Ruta.activa.is_(True)).order_by(Ruta.id)
    return list(session.scalars(statement))


def obtener_tarifa_vigente(session: Session, route_id: int | None, on_date=None) -> list[dict[str, object]]:
    from datetime import date
    requested_date = on_date or fecha_servicio()
    if not isinstance(requested_date, date):
        requested_date = date.fromisoformat(str(requested_date))
    day_type = tipo_dia(requested_date)
    statement = (
        select(Tarifa)
        .options(joinedload(Tarifa.ruta))
        .join(Tarifa.ruta)
        .where(Tarifa.activa.is_(True), Ruta.activa.is_(True), Tarifa.tipo_dia == day_type)
        .order_by(Ruta.id, Tarifa.id)
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
            "destination": fare.destino,
            "amount": fare.monto,
            "fecha_servicio": requested_date,
        }
        for fare in fares
    ]


def _obtener_ruta_activa(session: Session, route_id: int) -> Ruta:
    route = session.scalar(select(Ruta).where(Ruta.id == route_id, Ruta.activa.is_(True)))
    if route is None:
        raise ErrorDominio(404, "La ruta solicitada no existe o está inactiva.")
    return route


def _obtener_tarifa_ruta(session: Session, route_id: int, destination: str | None = None) -> Tarifa:
    day_type = tipo_dia(fecha_servicio())
    fare = session.scalar(select(Tarifa).where(
        Tarifa.ruta_id == route_id,
        Tarifa.tipo_dia == day_type,
        Tarifa.destino == destination,
        Tarifa.activa.is_(True),
    ))
    if fare is None:
        raise ErrorDominio(404, "La ruta no tiene una tarifa vigente.")
    return fare


def _validar_destino_ruta(session: Session, route_id: int, destination: str | None) -> None:
    destinations = set(session.scalars(select(Tarifa.destino).where(
        Tarifa.ruta_id == route_id,
        Tarifa.destino.is_not(None),
        Tarifa.activa.is_(True),
    )))
    if destinations and destination is None:
        raise ErrorDominio(422, "Selecciona un destino para esta ruta.")
    if destination is not None and destination not in destinations:
        raise ErrorDominio(422, "El destino indicado no corresponde a la ruta seleccionada.")