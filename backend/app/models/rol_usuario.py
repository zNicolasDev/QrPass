from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.rol import Rol
    from app.models.usuario import Usuario


class RolUsuario(Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        "user_id", ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    rol_id: Mapped[int] = mapped_column(
        "role_id", ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False
    )

    usuario: Mapped['Usuario'] = relationship(back_populates="roles")
    rol: Mapped['Rol'] = relationship(back_populates="usuarios")
