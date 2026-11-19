from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text

from app.models.base import Base


class Configuracion(Base):
    """Claves de configuración persistidas en la base de datos.

    Los catálogos (roles, perfiles, rutas y tarifas) viven aquí como JSON para
    que el repositorio no tenga que versionar datos semilla.
    """

    __tablename__ = "app_config"

    clave: Mapped[str] = mapped_column("clave", String(80), primary_key=True)
    valor: Mapped[str] = mapped_column("valor", Text, nullable=False)
