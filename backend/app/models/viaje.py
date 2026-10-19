from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.tarifa import Tarifa
    from app.models.pago import Pago
    from app.models.ruta import Ruta
    from app.models.turno import Turno
    from app.models.transbordo import Transbordo


# Registro de un abordaje, su ruta, costo y pago relacionado.
class Viaje(Base):
    # Viaje realizado: relaciona el pago con la ruta, tarifa y turno aplicados.
    __tablename__ = "trips"

    # Un viaje enlaza un pago con la tarifa, ruta y, si aplica, turno utilizado.
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pago_id: Mapped[int] = mapped_column(
        # unique=True impone como máximo un viaje asociado a cada pago.
        "payment_id", ForeignKey("payments.id", ondelete="RESTRICT"), unique=True, nullable=False
    )
    # El turno es opcional para pagos de pasajero que no pasan por el conductor.
    turno_id: Mapped[int | None] = mapped_column("shift_id", ForeignKey("shifts.id", ondelete="RESTRICT"))
    tarifa_id: Mapped[int] = mapped_column(
        "fare_id", ForeignKey("fares.id", ondelete="RESTRICT"), nullable=False
    )
    ruta_id: Mapped[int] = mapped_column(
        "route_id", ForeignKey("routes.id", ondelete="RESTRICT"), nullable=False
    )
    creado_en: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Estas relaciones permiten mostrar los datos asociados sin duplicarlos.
    pago: Mapped['Pago'] = relationship(back_populates="viaje")
    turno: Mapped["Turno | None"] = relationship(back_populates="viajes")
    tarifa: Mapped['Tarifa'] = relationship(back_populates="viajes")
    ruta: Mapped['Ruta'] = relationship(back_populates="viajes")
    transbordo_origen: Mapped["Transbordo | None"] = relationship(back_populates="viaje_origen", uselist=False)
