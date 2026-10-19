from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.sincronizacion_offline import SincronizacionOffline
    from app.models.vehiculo import Vehiculo


# Dispositivo que registra operaciónes realizadas a bordo.
class DispositivoAbordo(Base):
    # Identifica un equipo instalado en un vehículo para registrar actividad a bordo.
    __tablename__ = "boarding_devices"

    # Identificador del equipo y vehículo donde fue instalado.
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehiculo_id: Mapped[int] = mapped_column(
        "vehicle_id", ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=False
    )
    # Número de serie identifica físicamente el equipo y debe ser único.
    serie: Mapped[str] = mapped_column("serial", String(80), unique=True, nullable=False)

    # Un dispositivo pertenece a un vehículo y puede registrar varios eventos
    # de sincronización cuando se implemente el flujo offline.
    vehiculo: Mapped['Vehiculo'] = relationship(back_populates="dispositivos_abordo")
    # Una lista permite consultar todas las sincronizaciones relacionadas.
    eventos_sincronizacion: Mapped[list['SincronizacionOffline']] = relationship(
        back_populates="dispositivo"
    )
