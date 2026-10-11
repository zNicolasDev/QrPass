from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.pago import Pago
    from app.models.usuario import Usuario


class CodigoQr(Base):
    __tablename__ = "qr_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        "user_id", ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    estado: Mapped[str] = mapped_column("status", String(20), nullable=False, default="active")
    vence_en: Mapped[datetime] = mapped_column("expires_at", DateTime(timezone=True), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    usuario: Mapped['Usuario'] = relationship(back_populates="codigos_qr")
    pagos: Mapped[list['Pago']] = relationship(back_populates="codigo_qr")
