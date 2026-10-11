from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.turno import Turno
    from app.models.usuario import Usuario


class Conductor(Base):
    __tablename__ = "drivers"

    usuario_id: Mapped[int] = mapped_column(
        "user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    numero_licencia: Mapped[str] = mapped_column("license_number", String(50), unique=True, nullable=False)

    usuario: Mapped['Usuario'] = relationship(back_populates="conductor")
    turnos: Mapped[list['Turno']] = relationship(back_populates="conductor")
