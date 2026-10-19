from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.pago import Pago
    from app.models.usuario import Usuario


# QR temporal que identifica el turno y la ruta del bus.
class CodigoQr(Base):
    # El conductor del turno lo crea; varios pasajeros pueden escanearlo.
    __tablename__ = "qr_codes"

    # Identificador interno y conductor que presenta el código.
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        "user_id", ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # Token firmado que lee el escáner; no se permite guardar el mismo token dos veces.
    token: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    # El servicio cambia este estado entre activo, revocado o consumido.
    estado: Mapped[str] = mapped_column("status", String(20), nullable=False, default="active")
    # Fechas que determinan durante cuánto tiempo se puede validar el QR.
    vence_en: Mapped[datetime] = mapped_column("expires_at", DateTime(timezone=True), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Permite consultar quién presentó el QR y qué pagos se hicieron con él.
    usuario: Mapped['Usuario'] = relationship(back_populates="codigos_qr")
    pagos: Mapped[list['Pago']] = relationship(back_populates="codigo_qr")
