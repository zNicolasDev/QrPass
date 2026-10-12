from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.dispositivo_abordo import DispositivoAbordo


class SincronizacionOffline(Base):
    # Registro de sincronización asociado a un dispositivo (soporte de datos offline).
    __tablename__ = "offline_syncs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dispositivo_id: Mapped[int] = mapped_column(
        "device_id", ForeignKey("boarding_devices.id", ondelete="RESTRICT"), nullable=False
    )
    sincronizado_en: Mapped[datetime] = mapped_column(
        "synced_at", DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    dispositivo: Mapped['DispositivoAbordo'] = relationship(back_populates="eventos_sincronizacion")
