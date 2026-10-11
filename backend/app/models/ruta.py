from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.tarifa import Tarifa
    from app.models.turno import Turno
    from app.models.transbordo import Transbordo
    from app.models.viaje import Viaje


class Ruta(Base):
    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column("name", String(30), unique=True, nullable=False)
    activa: Mapped[bool] = mapped_column("active", Boolean, nullable=False, default=True)

    tarifas: Mapped[list['Tarifa']] = relationship(back_populates="ruta")
    turnos: Mapped[list['Turno']] = relationship(back_populates="ruta")
    viajes: Mapped[list['Viaje']] = relationship(back_populates="ruta")
    transbordos_destino: Mapped[list['Transbordo']] = relationship(back_populates="ruta_destino")
