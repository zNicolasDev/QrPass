from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.pago import Pago
    from app.models.usuario import Usuario


class Tarjeta(Base):
    # Medio de pago registrado para un usuario; no almacena aquí el número completo.
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        "user_id", ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    nombre_banco: Mapped[str] = mapped_column("bank_name", String(100), nullable=False)
    tipo_tarjeta: Mapped[str] = mapped_column("card_type", String(12), nullable=False)
    estado: Mapped[str] = mapped_column("status", String(20), nullable=False, default="active")

    usuario: Mapped['Usuario'] = relationship(back_populates="tarjetas")
    pagos: Mapped[list['Pago']] = relationship(back_populates="tarjeta")
