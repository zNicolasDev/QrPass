from __future__ import annotations
# Este módulo crea la conexión, prepara el esquema y entrega sesiones de base de datos.

import logging
import os
import sqlite3
from collections.abc import Generator
from pathlib import Path

from fastapi import Request
from sqlalchemy import Engine, create_engine, event, inspect, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base, Rol


DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[2] / "qrpass.db"
DEFAULT_DATABASE_URL = f"sqlite:///{DEFAULT_DATABASE_PATH.as_posix()}"

logger = logging.getLogger(__name__)

SYSTEM_ROLES = (
    ("PASSENGER", "Pasajero"),
    ("DRIVER", "Conductor"),
    ("ADMIN", "Administrador"),
)


class BaseDatos:
    def __init__(self, database_url: str | None = None) -> None:
        self.url = database_url or os.getenv("QR_PASS_DATABASE_URL", DEFAULT_DATABASE_URL)
        connect_args = {"check_same_thread": False} if self.url.startswith("sqlite") else {}
        engine_options: dict[str, object] = {"connect_args": connect_args}
        if self.url in {"sqlite://", "sqlite:///:memory:"}:
            engine_options["poolclass"] = StaticPool
        self.engine: Engine = create_engine(self.url, **engine_options)

        if self.url.startswith("sqlite"):
            event.listen(self.engine, "connect", self._enable_sqlite_foreign_keys)

        self.session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False,
        )

    @staticmethod
    def _enable_sqlite_foreign_keys(connection: sqlite3.Connection, _: object) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    def initialize(self) -> None:
        # Solo prepara el esquema y los catálogos del sistema. Los datos de
        # operación (rutas, tarifas, cuentas y turnos) se cargan de forma
        # explícita desde el comando de administración.
        Base.metadata.create_all(bind=self.engine)
        self._upgrade_sqlite_user_columns()
        self._upgrade_sqlite_fare_destinations()

        with self.session_factory() as session:
            for code, name in SYSTEM_ROLES:
                self._ensure_role(session, code, name)
            session.commit()

    def _upgrade_sqlite_user_columns(self) -> None:
        if not self.url.startswith("sqlite") or "://" not in self.url:
            return
        inspector = inspect(self.engine)
        if "users" not in inspector.get_table_names():
            return
        columns = {column["name"] for column in inspector.get_columns("users")}
        with self.engine.begin() as connection:
            if "username" not in columns:
                connection.exec_driver_sql("ALTER TABLE users ADD COLUMN username VARCHAR(80)")
            if "email" not in columns:
                connection.exec_driver_sql("ALTER TABLE users ADD COLUMN email VARCHAR(254)")
            if "password_hash" not in columns:
                connection.exec_driver_sql("ALTER TABLE users ADD COLUMN password_hash VARCHAR(256)")
            if "privacy_consent_at" not in columns:
                connection.exec_driver_sql(
                    "ALTER TABLE users ADD COLUMN privacy_consent_at DATETIME"
                )
            connection.exec_driver_sql(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)"
            )
            shift_columns = {column["name"] for column in inspect(self.engine).get_columns("shifts")}
            if "status" not in shift_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE shifts ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'active'"
                )
            if "cash_counted" not in shift_columns:
                connection.exec_driver_sql("ALTER TABLE shifts ADD COLUMN cash_counted INTEGER")
            if "cash_difference" not in shift_columns:
                connection.exec_driver_sql("ALTER TABLE shifts ADD COLUMN cash_difference INTEGER")
            payment_columns = {column["name"] for column in inspect(self.engine).get_columns("payments")}
            if "idempotency_key" not in payment_columns:
                connection.exec_driver_sql("ALTER TABLE payments ADD COLUMN idempotency_key VARCHAR(80)")
            connection.exec_driver_sql(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username)"
            )
            connection.exec_driver_sql(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_payments_user_idempotency "
                "ON payments (user_id, idempotency_key)"
            )

    def _upgrade_sqlite_fare_destinations(self) -> None:
        if not self.url.startswith("sqlite") or "://" not in self.url:
            return
        inspector = inspect(self.engine)
        if "fares" not in inspector.get_table_names():
            return
        if "destination" in {column["name"] for column in inspector.get_columns("fares")}:
            return

        connection = self.engine.raw_connection()
        try:
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=OFF")
            try:
                cursor.execute("BEGIN")
                cursor.execute(
                    "CREATE TABLE fares_new ("
                    "id INTEGER NOT NULL, "
                    "route_id INTEGER NOT NULL, "
                    "day_type VARCHAR(12) NOT NULL, "
                    "destination VARCHAR(60), "
                    "amount INTEGER NOT NULL, "
                    "active BOOLEAN NOT NULL, "
                    "PRIMARY KEY (id), "
                    "CONSTRAINT ck_fares_amount_positive CHECK (amount > 0), "
                    "CONSTRAINT ck_fares_day_type CHECK (day_type IN ('weekday', 'weekend')), "
                    "CONSTRAINT uq_fares_route_day_type_destination UNIQUE (route_id, day_type, destination), "
                    "FOREIGN KEY(route_id) REFERENCES routes (id) ON DELETE RESTRICT)"
                )
                cursor.execute(
                    "INSERT INTO fares_new (id, route_id, day_type, destination, amount, active) "
                    "SELECT id, route_id, day_type, NULL, amount, active FROM fares"
                )
                cursor.execute("DROP TABLE fares")
                cursor.execute("ALTER TABLE fares_new RENAME TO fares")
                cursor.execute(
                    "CREATE UNIQUE INDEX uq_fares_route_day_type_ordinary "
                    "ON fares (route_id, day_type) WHERE destination IS NULL"
                )
                if cursor.execute("PRAGMA foreign_key_check").fetchall():
                    raise RuntimeError("La actualización de la tabla de tarifas dejó viajes sin tarifa.")
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            connection.close()

    @staticmethod
    def _ensure_role(session: Session, code: str, name: str) -> Rol:
        role = session.query(Rol).filter_by(codigo=code).first()
        if role is None:
            role = Rol(codigo=code, nombre=name)
            session.add(role)
            session.flush()
        return role

    def close(self) -> None:
        self.engine.dispose()


def obtener_base_datos(request: Request) -> BaseDatos:
    return request.app.state.database


def verificar_conexion(database: BaseDatos) -> None:
    with database.engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def obtener_sesion(request: Request) -> Generator[Session, None, None]:
    database = obtener_base_datos(request)
    with database.session_factory() as session:
        yield session