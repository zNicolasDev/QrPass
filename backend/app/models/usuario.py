from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

# Estas importaciones solo ayudan al análisis de tipos; evitan ciclos en ejecución.
if TYPE_CHECKING:
    from app.models.tarjeta import Tarjeta
    from app.models.conductor import Conductor
    from app.models.pago import Pago
    from app.models.codigo_qr import CodigoQr
    from app.models.rol_usuario import RolUsuario


# Cuenta de la persona, su saldo y sus relaciones con pagos, roles, tarjetas y QR.
class Usuario(Base):
    # Cuenta principal; una persona puede tener pagos, QR, tarjetas y roles.
    __tablename__ = "users"
    __table_args__ = (
        # Regla también aplicada por la base: el saldo nunca puede ser negativo.
        CheckConstraint("wallet_balance >= 0", name="ck_users_wallet_nonnegative"),
    )

    # Mapped expresa el tipo Python; mapped_column define la columna SQL.
    # Estos campos guardan identidad, datos de acceso, consentimiento y saldo.
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombres: Mapped[str] = mapped_column("names", String(120), nullable=False)
    nombre_usuario: Mapped[str | None] = mapped_column("username", String(80), unique=True)
    correo: Mapped[str | None] = mapped_column("email", String(254), unique=True)
    hash_contrasena: Mapped[str | None] = mapped_column("password_hash", String(256))
    consentimiento_privacidad_en: Mapped[datetime | None] = mapped_column(
        "privacy_consent_at", DateTime(timezone=True)
    )
    numero_documento: Mapped[str] = mapped_column(
        "document_number", String(40), unique=True, nullable=False
    )
    saldo_billetera: Mapped[int] = mapped_column("wallet_balance", Integer, nullable=False, default=0)
    estado: Mapped[str] = mapped_column("status", String(20), nullable=False, default="active")

    # relationship crea navegación entre objetos; back_populates conecta ambos lados.
    pagos: Mapped[list['Pago']] = relationship(back_populates="usuario")
    codigos_qr: Mapped[list['CodigoQr']] = relationship(back_populates="usuario")
    tarjetas: Mapped[list['Tarjeta']] = relationship(back_populates="usuario")
    roles: Mapped[list['RolUsuario']] = relationship(back_populates="usuario")
    # uselist=False marca la relación opcional uno a uno con el perfil conductor.
    conductor: Mapped["Conductor | None"] = relationship(back_populates="usuario", uselist=False)
