from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.turno import Turno
    from app.models.usuario import Usuario


# Datos operativos asociados a una cuenta con rol de conductor.
class Conductor(Base):
    # Perfil operativo adicional: comparte su ID con la cuenta Usuario.
    __tablename__ = "drivers"

    # El ID también apunta a users.id: el perfil de conductor amplía una cuenta
    # existente en lugar de crear una identidad separada.
    usuario_id: Mapped[int] = mapped_column(
        # Es clave primaria y foránea: cada conductor corresponde a un usuario.
        "user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    # La licencia identifica el perfil operativo del conductor.
    numero_licencia: Mapped[str] = mapped_column("license_number", String(50), unique=True, nullable=False)

    # Desde el perfil se puede consultar su cuenta y todas sus jornadas.
    usuario: Mapped['Usuario'] = relationship(back_populates="conductor")
    turnos: Mapped[list['Turno']] = relationship(back_populates="conductor")
