from __future__ import annotations

from datetime import timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.dtos import CrearTransbordoSolicitud
from app.models import Usuario, Viaje, Pago, Transbordo, Ruta, Tarifa
from app.servicios.comun import ErrorDominio, ahora_servicio
from app.servicios.rutas_tarifas import _obtener_ruta_activa, _obtener_tarifa_ruta


def crear_transbordo(session: Session, user: Usuario, request: CrearTransbordoSolicitud) -> Transbordo:
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