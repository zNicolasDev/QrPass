from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.vehiculo import Vehiculo


class EmpresaTransporte(Base):
    __tablename__ = "transport_companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column("name", String(120), unique=True, nullable=False)

    vehiculos: Mapped[list['Vehiculo']] = relationship(back_populates="empresa")
