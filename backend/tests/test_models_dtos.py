from __future__ import annotations

from typing import cast

import pytest
from pydantic import ValidationError
from sqlalchemy import Table, create_engine, inspect
from sqlalchemy.orm import Session, configure_mappers

from app.dtos import (
    TipoTarjeta,
    CrearPagoSolicitud,
    MedioPago,
    RegistroPasajeroSolicitud,
    ValidacionQrPasajeroSolicitud,
    RutaRespuesta,
)
from app.models import Base, Pago, Tarifa, Ruta, Usuario


def test_models_register_domain_tables_relationships_and_invariants() -> None:
    configure_mappers()

    assert set(Base.metadata.tables) == {
        "users",
        "roles",
        "user_roles",
        "transport_companies",
        "routes",
        "fares",
        "drivers",
        "vehicles",
        "boarding_devices",
        "shifts",
        "cards",
        "qr_codes",
        "payments",
        "trips",
        "transfers",
        "offline_syncs",
    }
    assert Usuario.conductor.property.uselist is False
    assert Tarifa.ruta.property.uselist is False
    assert "saldo_anterior" in Pago.__mapper__.attrs
    assert "balance_before" not in Pago.__mapper__.attrs
    assert set(Base.metadata.tables["payments"].columns.keys()) == {
        "id",
        "user_id",
        "idempotency_key",
        "card_id",
        "qr_code_id",
        "method",
        "movement_type",
        "amount",
        "balance_before",
        "balance_after",
        "status",
        "created_at",
    }
    assert set(Base.metadata.tables["users"].columns.keys()) == {
        "id",
        "names",
        "username",
        "email",
        "password_hash",
        "privacy_consent_at",
        "document_number",
        "wallet_balance",
        "status",
    }
    assert set(Base.metadata.tables["routes"].columns.keys()) == {"id", "name", "active"}
    user_table = cast(Table, Usuario.__table__)
    assert any(
        constraint.name == "ck_users_wallet_nonnegative"
        for constraint in user_table.constraints
    )


def test_models_persist_and_load_related_route_and_fare() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            route = Ruta(nombre="ACADEMICA")
            fare = Tarifa(ruta=route, tipo_dia="weekday", monto=3300, activa=True)
            session.add(fare)
            session.commit()
            route_id = route.id
            fare_id = fare.id

        with Session(engine) as session:
            loaded_route = session.get(Ruta, route_id)
            loaded_fare = session.get(Tarifa, fare_id)
            assert loaded_route is not None
            assert loaded_fare is not None
            assert loaded_fare.ruta is loaded_route
            assert loaded_route.tarifas == [loaded_fare]
            assert "route_id" in {column["name"] for column in inspect(engine).get_columns("fares")}
    finally:
        engine.dispose()


def test_dto_validates_requests_and_serializes_model_output() -> None:
    route = Ruta(id=7, nombre="24")
    dto = RutaRespuesta.model_validate(route)

    assert dto.model_dump() == {"id": 7, "name": "24"}
    payment_request = CrearPagoSolicitud.model_validate(
        {"ruta_id": 7, "medio": MedioPago.CARD, "tipo_tarjeta": TipoTarjeta.DEBIT}
    )
    assert payment_request.tipo_tarjeta == TipoTarjeta.DEBIT
    assert payment_request.model_dump(mode="json") == {
        "route_id": 7,
        "method": "card",
        "card_type": "debit",
        "idempotency_key": None,
    }
    assert CrearPagoSolicitud.model_validate(
        {"route_id": 7, "method": "cash"}
    ).ruta_id == 7

    with pytest.raises(ValidationError):
        CrearPagoSolicitud.model_validate({"ruta_id": 7, "medio": MedioPago.CARD})
    with pytest.raises(ValidationError):
        CrearPagoSolicitud.model_validate({"ruta_id": 7, "medio": MedioPago.WALLET})
    with pytest.raises(ValidationError):
        CrearPagoSolicitud.model_validate(
            {"ruta_id": 7, "medio": MedioPago.CASH, "tipo_tarjeta": TipoTarjeta.CREDIT}
        )
    with pytest.raises(ValidationError):
        ValidacionQrPasajeroSolicitud.model_validate({"token": "muy-corto", "idempotency_key": "intento-qr-01"})
    with pytest.raises(ValidationError):
        RegistroPasajeroSolicitud.model_validate(
            {
                "nombres": "Ana Torres",
                "correo": "ana@example.com",
                "contrasena": "Clave-Segura-2026",
                "consentimiento_privacidad": False,
            }
        )
