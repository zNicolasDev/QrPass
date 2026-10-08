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

from aplicacion.modelos import (
    Base,
    Driver,
    Fare,
    Role,
    Route,
    Shift,
    TransportCompany,
    User,
    UserRole,
    Vehicle,
)
from aplicacion.contrasenas import hash_password


DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[1] / "qrpass.db"
DEFAULT_DATABASE_URL = f"sqlite:///{DEFAULT_DATABASE_PATH.as_posix()}"

DEMO_ROUTES = (
    "1", "2", "4/7", "6", "8/39", "9", "11", "14", "15", "17",
    "18", "19", "20", "21", "22", "23", "24", "28", "29", "31",
    "33", "35", "37", "40", "43", "48", "50", "53", "82",
)
logger = logging.getLogger(__name__)
DEMO_PASSENGER_USERNAME = "pasajero.demo"
DEMO_DRIVER_USERNAME = "conductor.demo"
DEMO_PASSENGER_PASSWORD = "QrPass-Pasajero-Demo-2026"
DEMO_DRIVER_PASSWORD = "QrPass-Conductor-Demo-2026"


class Database:
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

            passenger = session.get(User, 1)
            if passenger is None:
                passenger = User(
                    id=1,
                    names="María Camila",
                    document_number="DEMO-0001",
                    wallet_balance=50000,
                    status="active",
                )
                session.add(passenger)
            passenger.username = DEMO_PASSENGER_USERNAME
            passenger.email = "pasajero.demo@example.com"
            if passenger.password_hash is None:
                password = os.getenv("QR_PASS_DEMO_PASSENGER_PASSWORD", DEMO_PASSENGER_PASSWORD)
                passenger.password_hash = hash_password(password)
            self._ensure_user_role(session, passenger, passenger_role)

            driver_user = session.get(User, 2)
            if driver_user is None:
                driver_user = User(
                    id=2,
                    names="Carlos Andrés",
                    document_number="DEMO-0002",
                    wallet_balance=50000,
                    status="active",
                )
                session.add(driver_user)
            driver_user.username = DEMO_DRIVER_USERNAME
            driver_user.email = "conductor.demo@example.com"
            if driver_user.password_hash is None:
                password = os.getenv("QR_PASS_DEMO_DRIVER_PASSWORD", DEMO_DRIVER_PASSWORD)
                driver_user.password_hash = hash_password(password)
            self._ensure_user_role(session, driver_user, passenger_role)
            self._ensure_user_role(session, driver_user, driver_role)

            company = session.query(TransportCompany).filter_by(name="QrPass Empresa Demo").first()
            if company is None:
                company = TransportCompany(name="QrPass Empresa Demo")
                session.add(company)
                session.flush()
            vehicle = session.query(Vehicle).filter_by(plate="TUV-204").first()
            if vehicle is None:
                vehicle = Vehicle(company_id=company.id, plate="TUV-204")
                session.add(vehicle)
            driver = session.get(Driver, driver_user.id)
            if driver is None:
                driver = Driver(
                    user_id=driver_user.id,
                    license_number="LIC-DEMO-0002",
                )
                session.add(driver)

            for route_id, route_name in enumerate(DEMO_ROUTES, start=1):
                route = session.get(Route, route_id)
                if route is None:
                    route = Route(id=route_id, name=route_name)
                    session.add(route)
                    session.flush()
                for day_type, amount in (("weekday", 3300), ("weekend", 3400)):
                    fare = session.query(Fare).filter_by(
                        route_id=route_id,
                        day_type=day_type,
                    ).first()
                    if fare is None:
                        session.add(Fare(
                            route_id=route_id,
                            day_type=day_type,
                            amount=amount,
                            active=True,
                        ))

            session.flush()
            assigned_route = session.query(Route).filter_by(name="24").first()
            if assigned_route is None:
                raise RuntimeError("No se pudo preparar la ruta de la cuenta de conductor de demostración.")
            assignment = session.query(Shift).filter_by(
                driver_id=driver_user.id,
                vehicle_id=vehicle.id,
                route_id=assigned_route.id,
                ends_at=None,
            ).first()
            if assignment is None:
                session.add(Shift(
                    driver_id=driver_user.id,
                    vehicle_id=vehicle.id,
                    route_id=assigned_route.id,
                    starts_at=datetime.now(timezone.utc),
                    status="assigned",
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
    def _ensure_role(session: Session, code: str, name: str) -> Role:
        role = session.query(Role).filter_by(code=code).first()
        if role is None:
            role = Role(code=code, name=name)
            session.add(role)
            session.flush()
        return role

    @staticmethod
    def _ensure_user_role(session: Session, user: User, role: Role) -> None:
        assignment = session.query(UserRole).filter_by(
            user_id=user.id,
            role_id=role.id,
        ).first()
        if assignment is None:
            session.add(UserRole(user=user, role=role))

    def close(self) -> None:
        self.engine.dispose()


def get_database(request: Request) -> Database:
    return request.app.state.database


def get_session(request: Request) -> Generator[Session, None, None]:
    database = get_database(request)
    with database.session_factory() as session:
        yield session
