from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.tarjeta import Tarjeta
    from app.models.codigo_qr import CodigoQr
    from app.models.viaje import Viaje
    from app.models.usuario import Usuario


class Pago(Base):
    # Registro financiero interno: conserva importe, saldos y medio utilizado.
    __tablename__ = "payments"
    __table_args__ = (
        # Constraints hacen que la base también proteja invariantes importantes.
        CheckConstraint("amount >= 0", name="ck_payments_amount_nonnegative"),
        CheckConstraint("balance_before >= 0", name="ck_payments_balance_before_nonnegative"),
        CheckConstraint("balance_after >= 0", name="ck_payments_balance_after_nonnegative"),
        # El mismo usuario no puede registrar dos veces una misma clave de reintento.
        UniqueConstraint("user_id", "idempotency_key", name="uq_payments_user_idempotency_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        # El primer argumento conserva el nombre físico en inglés en la tabla.
        "user_id", ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    clave_idempotencia: Mapped[str | None] = mapped_column("idempotency_key", String(80))
    tarjeta_id: Mapped[int | None] = mapped_column(
        "card_id", ForeignKey("cards.id", ondelete="RESTRICT")
    )
    codigo_qr_id: Mapped[int | None] = mapped_column(
        "qr_code_id", ForeignKey("qr_codes.id", ondelete="RESTRICT")
    )
    medio: Mapped[str] = mapped_column("method", String(20), nullable=False)
    tipo_movimiento: Mapped[str] = mapped_column("movement_type", String(20), nullable=False)
    monto: Mapped[int] = mapped_column("amount", Integer, nullable=False)
    saldo_anterior: Mapped[int] = mapped_column("balance_before", Integer, nullable=False)
    saldo_posterior: Mapped[int] = mapped_column("balance_after", Integer, nullable=False)
    estado: Mapped[str] = mapped_column("status", String(20), nullable=False, default="completed")
    creado_en: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    usuario: Mapped['Usuario'] = relationship(back_populates="pagos")
    tarjeta: Mapped["Tarjeta | None"] = relationship(back_populates="pagos")
    codigo_qr: Mapped["CodigoQr | None"] = relationship(back_populates="pagos")
    # Un pago puede no ser un viaje (p. ej., una recarga); si lo es, es único.
    viaje: Mapped["Viaje | None"] = relationship(back_populates="pago", uselist=False)
