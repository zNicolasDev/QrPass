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


class Viaje(Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pago_id: Mapped[int] = mapped_column(
        "payment_id", ForeignKey("payments.id", ondelete="RESTRICT"), unique=True, nullable=False
    )
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

    pago: Mapped['Pago'] = relationship(back_populates="viaje")
    turno: Mapped["Turno | None"] = relationship(back_populates="viajes")
    tarifa: Mapped['Tarifa'] = relationship(back_populates="viajes")
    ruta: Mapped['Ruta'] = relationship(back_populates="viajes")
    transbordo_origen: Mapped["Transbordo | None"] = relationship(back_populates="viaje_origen", uselist=False)
