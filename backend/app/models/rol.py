from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.rol_usuario import RolUsuario


class Rol(Base):
    # Catálogo de permisos; el código (PASSENGER, DRIVER) se usa en verificaciones.
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column("code", String(40), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column("name", String(80), nullable=False)

    usuarios: Mapped[list['RolUsuario']] = relationship(back_populates="rol")
