from __future__ import annotations

import os
import logging
import sqlite3
from collections.abc import Generator
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Request
from sqlalchemy import Engine, create_engine, event, inspect
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import (
    Base,
    Conductor,
    Tarifa,
    Rol,
    Ruta,
    Turno,
    EmpresaTransporte,
    Usuario,
    RolUsuario,
    Vehiculo,
)
from app.passwords import crear_hash_contrasena


DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[1] / "qrpass.db"
DEFAULT_DATABASE_URL = f"sqlite:///{DEFAULT_DATABASE_PATH.as_posix()}"

DEMO_ROUTES = (
    "1", "2", "4/7", "6", "8/39", "9", "11", "14", "15", "17",
    "18", "19", "20", "21", "22", "23", "24", "28", "29", "31",
    "33", "35", "37", "40", "43", "48", "50", "53", "82", "90", "ALIMENTADOR CHUCHUNI", "SAN BERNARDO-SALADO",
)
logger = logging.getLogger(__name__)
DEMO_PASSENGER_USERNAME = "pasajero.demo"
DEMO_DRIVER_USERNAME = "conductor.demo"
DEMO_PASSENGER_PASSWORD = "QrPass-Pasajero-Demo-2026"
DEMO_DRIVER_PASSWORD = "QrPass-Conductor-Demo-2026"


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
        Base.metadata.create_all(bind=self.engine)
        self._upgrade_sqlite_user_columns()
        with self.session_factory() as session:
            passenger_role = self._ensure_role(session, "PASSENGER", "Pasajero")
            driver_role = self._ensure_role(session, "DRIVER", "Conductor")

            passenger = session.get(Usuario, 1)
            if passenger is None:
                passenger = Usuario(
                    id=1,
                    nombres="María Camila",
                    numero_documento="DEMO-0001",
                    saldo_billetera=50000,
                    estado="active",
                )
                session.add(passenger)
            passenger.nombre_usuario = DEMO_PASSENGER_USERNAME
            passenger.correo = "pasajero.demo@example.com"
            if passenger.hash_contrasena is None:
                password = os.getenv("QR_PASS_DEMO_PASSENGER_PASSWORD", DEMO_PASSENGER_PASSWORD)
                passenger.hash_contrasena = crear_hash_contrasena(password)
            self._ensure_user_role(session, passenger, passenger_role)

            driver_user = session.get(Usuario, 2)
            if driver_user is None:
                driver_user = Usuario(
                    id=2,
                    nombres="Carlos Andrés",
                    numero_documento="DEMO-0002",
                    saldo_billetera=50000,
                    estado="active",
                )
                session.add(driver_user)
            driver_user.nombre_usuario = DEMO_DRIVER_USERNAME
            driver_user.correo = "conductor.demo@example.com"
            if driver_user.hash_contrasena is None:
                password = os.getenv("QR_PASS_DEMO_DRIVER_PASSWORD", DEMO_DRIVER_PASSWORD)
                driver_user.hash_contrasena = crear_hash_contrasena(password)
            self._ensure_user_role(session, driver_user, passenger_role)
            self._ensure_user_role(session, driver_user, driver_role)

            company = session.query(EmpresaTransporte).filter_by(nombre="QrPass Empresa Demo").first()
            if company is None:
                company = EmpresaTransporte(nombre="QrPass Empresa Demo")
                session.add(company)
                session.flush()
            vehicle = session.query(Vehiculo).filter_by(placa="TUV-204").first()
            if vehicle is None:
                vehicle = Vehiculo(empresa_id=company.id, placa="TUV-204")
                session.add(vehicle)
            driver = session.get(Conductor, driver_user.id)
            if driver is None:
                driver = Conductor(
                    usuario_id=driver_user.id,
                    numero_licencia="LIC-DEMO-0002",
                )
                session.add(driver)

            for route_id, route_name in enumerate(DEMO_ROUTES, start=1):
                route = session.get(Ruta, route_id)
                if route is None:
                    route = Ruta(id=route_id, nombre=route_name)
                    session.add(route)
                    session.flush()
                for day_type, amount in (("weekday", 3300), ("weekend", 3400)):
                    fare = session.query(Tarifa).filter_by(
                        ruta_id=route_id,
                        tipo_dia=day_type,
                    ).first()
                    if fare is None:
                        session.add(Tarifa(
                            ruta_id=route_id,
                            tipo_dia=day_type,
                            monto=amount,
                            activa=True,
                        ))

            session.flush()
            assigned_route = session.query(Ruta).filter_by(nombre="24").first()
            if assigned_route is None:
                raise RuntimeError("No se pudo preparar la ruta de la cuenta de conductor de demostración.")
            assignment = session.query(Turno).filter_by(
                conductor_id=driver_user.id,
                vehiculo_id=vehicle.id,
                ruta_id=assigned_route.id,
                finaliza_en=None,
            ).first()
            if assignment is None:
                session.add(Turno(
                    conductor_id=driver_user.id,
                    vehiculo_id=vehicle.id,
                    ruta_id=assigned_route.id,
                    inicia_en=datetime.now(timezone.utc),
                    estado="assigned",
                ))

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

    @staticmethod
    def _ensure_role(session: Session, code: str, name: str) -> Rol:
        role = session.query(Rol).filter_by(codigo=code).first()
        if role is None:
            role = Rol(codigo=code, nombre=name)
            session.add(role)
            session.flush()
        return role

    @staticmethod
    def _ensure_user_role(session: Session, user: Usuario, role: Rol) -> None:
        assignment = session.query(RolUsuario).filter_by(
            usuario_id=user.id,
            rol_id=role.id,
        ).first()
        if assignment is None:
            session.add(RolUsuario(usuario=user, rol=role))

    def close(self) -> None:
        self.engine.dispose()


def obtener_base_datos(request: Request) -> BaseDatos:
    return request.app.state.database


def obtener_sesion(request: Request) -> Generator[Session, None, None]:
    database = obtener_base_datos(request)
    with database.session_factory() as session:
        yield session
