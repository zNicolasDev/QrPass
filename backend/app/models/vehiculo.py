from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.dispositivo_abordo import DispositivoAbordo
    from app.models.turno import Turno
    from app.models.empresa_transporte import EmpresaTransporte


class Vehiculo(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(
        "company_id", ForeignKey("transport_companies.id", ondelete="RESTRICT"), nullable=False
    )
    placa: Mapped[str] = mapped_column("plate", String(12), unique=True, nullable=False)

    empresa: Mapped['EmpresaTransporte'] = relationship(back_populates="vehiculos")
    turnos: Mapped[list['Turno']] = relationship(back_populates="vehiculo")
    dispositivos_abordo: Mapped[list['DispositivoAbordo']] = relationship(back_populates="vehiculo")
