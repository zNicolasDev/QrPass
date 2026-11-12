from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models import Usuario, Turno, Viaje, Transbordo, Ruta, Pago


def obtener_metricas_gerenciales(session: Session) -> dict[str, int]:
    rows = session.execute(
        select(Pago.medio, func.sum(Pago.monto), func.count(Pago.id))
        .where(Pago.tipo_movimiento == "fare_payment")
        .group_by(Pago.medio)
    ).all()

    recaudo_efectivo = 0
    recaudo_qr = 0
    recaudo_tarjeta = 0
    total_recaudado = 0

    for method, amount, _ in rows:
        monto = int(amount or 0)
        total_recaudado += monto
        if method == "cash":
            recaudo_efectivo += monto
        elif method == "wallet":
            recaudo_qr += monto
        elif method.startswith("card_"):
            recaudo_tarjeta += monto

    total_viajes = session.scalar(select(func.count(Viaje.id))) or 0
    total_transbordos = session.scalar(select(func.count(Transbordo.id))) or 0
    turnos_activos = session.scalar(select(func.count(Turno.id)).where(Turno.estado == "active")) or 0
    total_usuarios = session.scalar(select(func.count(Usuario.id))) or 0
    total_rutas = session.scalar(select(func.count(Ruta.id))) or 0

    return {
        "total_collected": total_recaudado,
        "cash_collected": recaudo_efectivo,
        "qr_collected": recaudo_qr,
        "card_collected": recaudo_tarjeta,
        "total_trips": int(total_viajes),
        "total_transfers": int(total_transbordos),
        "active_shifts": int(turnos_activos),
        "total_users": int(total_usuarios),
        "total_routes": int(total_rutas),
    }
