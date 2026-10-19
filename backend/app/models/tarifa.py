from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.ruta import Ruta
    from app.models.viaje import Viaje


# Valor del viaje para una ruta y tipo de día.
class Tarifa(Base):
    # Precio de una ruta según tipo de día; cada viaje guarda qué tarifa usó.
    __tablename__ = "fares"
    __table_args__ = (
        # Validaciones y unicidad se hacen cumplir en la propia base de datos.
        CheckConstraint("amount > 0", name="ck_fares_amount_positive"),
        CheckConstraint("day_type IN ('weekday', 'weekend')", name="ck_fares_day_type"),
        UniqueConstraint("route_id", "day_type", name="uq_fares_route_day_type"),
    )

    # La tarifa pertenece a una ruta y define tipo de día, valor y disponibilidad.
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ruta_id: Mapped[int] = mapped_column(
        "route_id", ForeignKey("routes.id", ondelete="RESTRICT"), nullable=False
    )
    tipo_dia: Mapped[str] = mapped_column("day_type", String(12), nullable=False)
    monto: Mapped[int] = mapped_column("amount", Integer, nullable=False)
    activa: Mapped[bool] = mapped_column("active", Boolean, nullable=False, default=True)

    # Una tarifa se usa en los viajes que se cobran con ese valor.
    ruta: Mapped['Ruta'] = relationship(back_populates="tarifas")
    viajes: Mapped[list['Viaje']] = relationship(back_populates="tarifa")
