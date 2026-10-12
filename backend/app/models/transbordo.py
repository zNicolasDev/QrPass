from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.ruta import Ruta
    from app.models.viaje import Viaje


class Transbordo(Base):
    # Registra la ruta destino solicitada a partir de un viaje previo.
    __tablename__ = "transfers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    viaje_origen_id: Mapped[int] = mapped_column(
        # unique=True limita a un solo transbordo de origen por viaje.
        "origin_trip_id", ForeignKey("trips.id", ondelete="RESTRICT"), unique=True, nullable=False
    )
    ruta_destino_id: Mapped[int] = mapped_column(
        "destination_route_id", ForeignKey("routes.id", ondelete="RESTRICT"), nullable=False
    )
    creado_en: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    viaje_origen: Mapped['Viaje'] = relationship(back_populates="transbordo_origen")
    ruta_destino: Mapped['Ruta'] = relationship(back_populates="transbordos_destino")
