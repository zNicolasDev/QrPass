from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.conductor import Conductor
    from app.models.ruta import Ruta
    from app.models.viaje import Viaje
    from app.models.vehiculo import Vehiculo


# Jornada asignada al conductor, con ruta, vehículo y horarios.
class Turno(Base):
    # Jornada de un conductor en un vehículo y una ruta.
    __tablename__ = "shifts"
    __table_args__ = (
        # Permite turno abierto (sin fin); si termina, no puede acabar antes de iniciar.
        CheckConstraint("ends_at IS NULL OR ends_at >= starts_at", name="ck_shifts_valid_dates"),
    )

    # Identificador de la jornada y claves que asignan conductor, vehículo y ruta.
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conductor_id: Mapped[int] = mapped_column(
        "driver_id", ForeignKey("drivers.user_id", ondelete="RESTRICT"), nullable=False
    )
    vehiculo_id: Mapped[int] = mapped_column(
        "vehicle_id", ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=False
    )
    ruta_id: Mapped[int] = mapped_column(
        "route_id", ForeignKey("routes.id", ondelete="RESTRICT"), nullable=False
    )
    # El inicio es obligatorio; el final queda vacío mientras el turno esté abierto.
    inicia_en: Mapped[datetime] = mapped_column("starts_at", DateTime(timezone=True), nullable=False)
    finaliza_en: Mapped[datetime | None] = mapped_column("ends_at", DateTime(timezone=True))
    # Estado y datos de cierre para calcular la diferencia de efectivo.
    estado: Mapped[str] = mapped_column("status", String(20), nullable=False, default="active")
    efectivo_contado: Mapped[int | None] = mapped_column("cash_counted", Integer)
    diferencia_efectivo: Mapped[int | None] = mapped_column("cash_difference", Integer)

    # Relaciones para navegar desde el turno a sus participantes y viajes cobrados.
    conductor: Mapped['Conductor'] = relationship(back_populates="turnos")
    vehiculo: Mapped['Vehiculo'] = relationship(back_populates="turnos")
    ruta: Mapped['Ruta'] = relationship(back_populates="turnos")
    viajes: Mapped[list['Viaje']] = relationship(back_populates="turno")
