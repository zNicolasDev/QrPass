from collections.abc import Iterator
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.exc import OperationalError
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

import app.services as services
from app.main import crear_aplicacion


def auth_headers(client: TestClient, username: str = "pasajero.demo") -> dict[str, str]:
    password = {
        "pasajero.demo": "QrPass-Pasajero-Demo-2026",
        "conductor.demo": "QrPass-Conductor-Demo-2026",
    }[username]
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def start_driver(client: TestClient, headers: dict[str, str]) -> None:
    assignment = client.get("/api/v1/driver/demo/assignment", headers=headers)
    assert assignment.status_code == 200
    response = client.post(
        "/api/v1/driver/shift/start",
        params={"route_id": assignment.json()["route_id"]},
        headers=headers,
    )
    assert response.status_code == 200


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    # Cada escenario arranca con una base de datos de memoria propia; así un
    # pago de una prueba no cambia el saldo con el que comienza la siguiente.
    # Los flujos generales usan un día hábil fijo; las pruebas de calendario
    # indican su propia fecha y también cubren fines de semana y festivos.
    monkeypatch.setattr(services, "fecha_servicio", lambda: date(2026, 10, 19))
    application = crear_aplicacion("sqlite://")
    with TestClient(application, raise_server_exceptions=False) as test_client:
        yield test_client


def test_health_routes_and_demo_seed(client: TestClient) -> None:
    assert client.get("/api/v1/health").json() == {
        "status": "ok",
        "service": "qrpass-api",
        "mode": "demo",
    }
    endpoint_listar_rutas = client.get("/api/v1/routes")
    assert endpoint_listar_rutas.status_code == 200
    assert len(endpoint_listar_rutas.json()) == 32
    headers = auth_headers(client)
    assert client.get("/api/v1/demo/account", headers=headers).json()["wallet_balance"] == 50000


def test_readiness_checks_database_and_reports_unavailability(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ready = client.get("/api/v1/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"

    def fail_connection(_: Engine):
        raise OperationalError("SELECT 1", {}, RuntimeError("database unavailable"))

    monkeypatch.setattr(Engine, "connect", fail_connection)
    unavailable = client.get("/api/v1/ready")

    assert unavailable.status_code == 503
    assert unavailable.json()["detail"] == "La base de datos no está disponible."


def test_passenger_login_and_authenticated_identity(client: TestClient) -> None:
    endpoint_iniciar_sesion = client.post(
        "/api/v1/auth/login",
        json={"username": "pasajero.demo", "password": "QrPass-Pasajero-Demo-2026"},
    )

    assert endpoint_iniciar_sesion.status_code == 200
    assert endpoint_iniciar_sesion.json()["user"]["roles"] == ["PASSENGER"]
    assert endpoint_iniciar_sesion.json()["expires_in"] == 3600
    headers = {"Authorization": f"Bearer {endpoint_iniciar_sesion.json()['access_token']}"}
    endpoint_usuario_actual = client.get("/api/v1/auth/me", headers=headers)
    assert endpoint_usuario_actual.status_code == 200
    assert endpoint_usuario_actual.json()["username"] == "pasajero.demo"
    assert client.get("/api/v1/driver/demo/assignment", headers=headers).status_code == 403


def test_driver_login_has_both_roles_and_can_read_assignment(client: TestClient) -> None:
    endpoint_iniciar_sesion = client.post(
        "/api/v1/auth/login",
        json={"username": "conductor.demo", "password": "QrPass-Conductor-Demo-2026"},
    )

    assert endpoint_iniciar_sesion.status_code == 200
    assert endpoint_iniciar_sesion.json()["user"]["roles"] == ["DRIVER", "PASSENGER"]
    headers = {"Authorization": f"Bearer {endpoint_iniciar_sesion.json()['access_token']}"}
    assignment = client.get("/api/v1/driver/demo/assignment", headers=headers)
    assert assignment.status_code == 200
    assert assignment.json()["route_name"] == "24"
    assert assignment.json()["vehicle_plate"] == "TUV-204"


def test_authentication_rejects_bad_credentials_missing_and_tampered_tokens(client: TestClient) -> None:
    failed_login = client.post(
        "/api/v1/auth/login",
        json={"username": "conductor.demo", "password": "incorrecta"},
    )
    assert failed_login.status_code == 401
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer fake.payload"},
    ).status_code == 401


def test_passenger_registration_creates_only_passenger_role_and_isolated_wallet(client: TestClient) -> None:
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "names": "  Ana   Torres ",
            "email": "ANA.TORRES@example.com",
            "password": "ContraseñaSegura-2026",
            "privacy_consent": True,
        },
    )
    assert registration.status_code == 201
    assert registration.json()["email"] == "ana.torres@example.com"
    assert registration.json()["roles"] == ["PASSENGER"]
    assert client.post(
        "/api/v1/auth/register",
        json={
            "names": "Ana Torres",
            "email": "ana.torres@example.com",
            "password": "ContraseñaSegura-2026",
            "privacy_consent": True,
        },
    ).status_code == 409
    endpoint_iniciar_sesion = client.post(
        "/api/v1/auth/login",
        json={"username": "ana.torres@example.com", "password": "ContraseñaSegura-2026"},
    )
    headers = {"Authorization": f"Bearer {endpoint_iniciar_sesion.json()['access_token']}"}
    assert client.get("/api/v1/demo/account", headers=headers).json()["wallet_balance"] == 0
    assert client.get("/api/v1/driver/demo/assignment", headers=headers).status_code == 403
    assert client.get("/api/v1/demo/account").status_code == 401


def test_authenticated_payment_is_idempotent(client: TestClient) -> None:
    headers = auth_headers(client)
    data = {"route_id": 1, "method": "wallet", "idempotency_key": "payment-retry-0001"}
    first = client.post("/api/v1/demo/account/payments", json=data, headers=headers)
    retry = client.post("/api/v1/demo/account/payments", json=data, headers=headers)

    assert first.status_code == retry.status_code == 201
    assert first.json()["payment_id"] == retry.json()["payment_id"]
    assert client.get("/api/v1/demo/account", headers=headers).json()["wallet_balance"] == 46700
    assert len(client.get("/api/v1/demo/account/trips", headers=headers).json()) == 1


def test_failed_payment_commit_rolls_back_balance_payment_and_trip(client: TestClient) -> None:
    headers = auth_headers(client)

    def fail_before_commit(_: Session) -> None:
        raise RuntimeError("injected failure before commit")

    event.listen(Session, "before_commit", fail_before_commit)
    try:
        failed_payment = client.post(
            "/api/v1/demo/account/payments",
            json={"route_id": 1, "method": "wallet", "idempotency_key": "atomic-failure-001"},
            headers=headers,
        )
    finally:
        event.remove(Session, "before_commit", fail_before_commit)

    assert failed_payment.status_code == 500
    assert client.get("/api/v1/demo/account", headers=headers).json()["wallet_balance"] == 50000
    assert client.get("/api/v1/payments/history", headers=headers).json() == []
    assert client.get("/api/v1/trips", headers=headers).json() == []


def test_failed_qr_redemption_commit_restores_qr_balance_payment_and_trip(client: TestClient) -> None:
    passenger = auth_headers(client)
    driver = auth_headers(client, "conductor.demo")
    assignment = client.get("/api/v1/driver/demo/assignment", headers=driver).json()
    start_driver(client, driver)
    qr = client.post(
        "/api/v1/demo/account/qr",
        json={"route_id": assignment["route_id"]},
        headers=passenger,
    ).json()
    scan = {"token": qr["token"], "idempotency_key": "atomic-qr-failure-001"}

    def fail_before_commit(_: Session) -> None:
        raise RuntimeError("injected failure before commit")

    event.listen(Session, "before_commit", fail_before_commit)
    try:
        failed_redemption = client.post(
            "/api/v1/driver/qr/validate",
            json=scan,
            headers=driver,
        )
    finally:
        event.remove(Session, "before_commit", fail_before_commit)

    assert failed_redemption.status_code == 500
    assert client.get("/api/v1/demo/account", headers=passenger).json()["wallet_balance"] == 50000
    assert client.get("/api/v1/payments/history", headers=passenger).json() == []

    retry = client.post("/api/v1/driver/qr/validate", json=scan, headers=driver)

    assert retry.status_code == 201
    assert client.get("/api/v1/demo/account", headers=passenger).json()["wallet_balance"] == 46700
    assert len(client.get("/api/v1/payments/history", headers=passenger).json()) == 1
    assert len(client.get("/api/v1/trips", headers=passenger).json()) == 1


def test_payment_history_includes_top_ups_and_fare_payments(client: TestClient) -> None:
    headers = auth_headers(client)
    top_up = client.post(
        "/api/v1/demo/account/top-ups",
        json={"amount": 10000, "idempotency_key": "history-top-up-001"},
        headers=headers,
    )
    fare = client.post(
        "/api/v1/demo/account/payments",
        json={"route_id": 1, "method": "wallet", "idempotency_key": "history-fare-0001"},
        headers=headers,
    )

    history = client.get("/api/v1/payments/history", headers=headers)

    assert top_up.status_code == fare.status_code == 201
    assert history.status_code == 200
    assert [item["movement_type"] for item in history.json()] == ["fare_payment", "top_up"]
    assert history.json()[0]["trip_id"] == fare.json()["trip_id"]
    assert history.json()[0]["balance_before"] == 60000
    assert history.json()[0]["balance_after"] == 56700
    assert history.json()[1]["trip_id"] is None
    assert history.json()[1]["balance_after"] == 60000
    assert client.get("/api/v1/payments/history").status_code == 401


def test_trip_resource_lists_and_returns_only_the_owners_trip(client: TestClient) -> None:
    headers = auth_headers(client)
    payment = client.post(
        "/api/v1/demo/account/payments",
        json={"route_id": 1, "method": "wallet"},
        headers=headers,
    )
    trip_id = payment.json()["trip_id"]

    trips = client.get("/api/v1/trips", headers=headers)
    detail = client.get(f"/api/v1/trips/{trip_id}", headers=headers)
    missing = client.get("/api/v1/trips/999999", headers=headers)

    assert trips.status_code == detail.status_code == 200
    assert len(trips.json()) == 1
    assert detail.json() == trips.json()[0]
    assert missing.status_code == 404
    assert client.get(f"/api/v1/trips/{trip_id}").status_code == 401


def test_top_up_is_idempotent_and_credits_wallet_once(client: TestClient) -> None:
    headers = auth_headers(client)
    request = {"amount": 10000, "idempotency_key": "top-up-retry-0001"}
    first = client.post("/api/v1/demo/account/top-ups", json=request, headers=headers)
    retry = client.post("/api/v1/demo/account/top-ups", json=request, headers=headers)
    changed_amount = client.post(
        "/api/v1/demo/account/top-ups",
        json={**request, "amount": 20000},
        headers=headers,
    )

    assert first.status_code == retry.status_code == 201
    assert first.json()["payment_id"] == retry.json()["payment_id"]
    assert changed_amount.status_code == 409
    assert client.get("/api/v1/demo/account", headers=headers).json()["wallet_balance"] == 60000


def test_driver_records_cash_and_closes_immutable_server_shift(client: TestClient) -> None:
    headers = auth_headers(client, "conductor.demo")
    start_driver(client, headers)
    cash = client.post(
        "/api/v1/driver/shift/payments",
        json={"method": "cash", "idempotency_key": "driver-cash-0001"},
        headers=headers,
    )
    shift = client.get("/api/v1/driver/shift", headers=headers)
    closed = client.post("/api/v1/driver/shift/close", json={"cash_counted": 3300}, headers=headers)

    assert cash.status_code == 201
    assert shift.status_code == 200
    assert shift.json()["cash_total"] == 3300
    assert shift.json()["payment_count"] == 1
    assert closed.status_code == 200
    assert closed.json()["shift"]["cash_total"] == 3300
    assert closed.json()["shift"]["cash_counted"] == 3300
    assert closed.json()["shift"]["cash_difference"] == 0
    assert closed.json()["closed"] is True
    assert client.get("/api/v1/driver/shift", headers=headers).status_code == 404
    history = client.get("/api/v1/driver/shifts/history", headers=headers)
    assert history.status_code == 200
    assert history.json()[0]["shift_id"] == closed.json()["shift"]["shift_id"]
    assert history.json()[0]["cash_counted"] == 3300
    assert client.get("/api/v1/driver/shifts/history").status_code == 401
    assert client.post(
        "/api/v1/driver/shift/payments",
        json={"method": "cash", "idempotency_key": "driver-cash-0002"},
        headers=headers,
    ).status_code == 409


def test_saturday_sunday_and_colombian_holiday_fares(client: TestClient) -> None:
    weekday = client.get("/api/v1/fares/current", params={"route_id": 1, "on_date": "2026-10-08"})
    saturday = client.get("/api/v1/fares/current", params={"route_id": 1, "on_date": "2026-10-10"})
    sunday = client.get("/api/v1/fares/current", params={"route_id": 1, "on_date": "2026-10-11"})
    holiday = client.get("/api/v1/fares/current", params={"route_id": 1, "on_date": "2026-10-12"})

    assert weekday.status_code == 200
    assert weekday.json()[0]["amount"] == 3300
    assert weekday.json()[0]["day_type"] == "weekday"
    assert saturday.json()[0]["amount"] == 3300
    assert saturday.json()[0]["day_type"] == "weekday"
    assert sunday.json()[0]["amount"] == 3400
    assert sunday.json()[0]["day_type"] == "weekend"
    assert holiday.json()[0]["amount"] == 3400
    assert holiday.json()[0]["day_type"] == "weekend"


def test_wallet_payment_updates_balance_and_trip_history(client: TestClient) -> None:
    headers = auth_headers(client)
    payment = client.post(
        "/api/v1/demo/account/payments",
        json={"route_id": 1, "method": "wallet"},
        headers=headers,
    )

    assert payment.status_code == 201
    assert payment.json()["amount"] == 3300
    assert payment.json()["wallet_balance"] == 46700
    history = client.get("/api/v1/demo/account/trips", headers=headers)
    assert len(history.json()) == 1
    assert history.json()[0]["route_name"] == "1"


def test_cash_and_card_payments_do_not_change_wallet(client: TestClient) -> None:
    headers = auth_headers(client)
    cash = client.post(
        "/api/v1/demo/account/payments",
        json={"route_id": 1, "method": "cash"},
        headers=headers,
    )
    card = client.post(
        "/api/v1/demo/account/payments",
        json={"route_id": 2, "method": "card", "card_type": "credit"},
        headers=headers,
    )

    assert cash.status_code == 201
    assert card.status_code == 201
    assert card.json()["method"] == "card_credit"
    assert cash.json()["wallet_balance"] == 50000
    assert card.json()["wallet_balance"] == 50000


def test_card_requires_a_supported_card_type(client: TestClient) -> None:
    headers = auth_headers(client)
    missing_type = client.post(
        "/api/v1/demo/account/payments",
        json={"route_id": 1, "method": "card"},
        headers=headers,
    )
    unsupported_type = client.post(
        "/api/v1/demo/account/payments",
        json={"route_id": 1, "method": "card", "card_type": "prepaid"},
        headers=headers,
    )

    assert missing_type.status_code == 422
    assert unsupported_type.status_code == 422


def test_insufficient_balance_does_not_create_a_trip(client: TestClient) -> None:
    headers = auth_headers(client)
    for _ in range(15):
        successful_payment = client.post(
            "/api/v1/demo/account/payments",
            json={"route_id": 1, "method": "wallet"},
            headers=headers,
        )
        assert successful_payment.status_code == 201

    payment = client.post(
        "/api/v1/demo/account/payments",
        json={"route_id": 1, "method": "wallet"},
        headers=headers,
    )

    assert payment.status_code == 409
    assert client.get("/api/v1/demo/account", headers=headers).json()["wallet_balance"] == 500
    assert len(client.get("/api/v1/demo/account/trips", headers=headers).json()) == 15


def test_top_up_limits_and_transfer_rules(client: TestClient) -> None:
    headers = auth_headers(client)
    invalid_top_up = client.post("/api/v1/demo/account/top-ups", json={"amount": 500001}, headers=headers)
    assert invalid_top_up.status_code == 422

    payment = client.post(
        "/api/v1/demo/account/payments",
        json={"route_id": 1, "method": "wallet"},
        headers=headers,
    )
    trip_id = payment.json()["trip_id"]
    transfer = client.post(
        "/api/v1/demo/account/transfers",
        json={"trip_id": trip_id, "destination_route_id": 2},
        headers=headers,
    )
    repeated_transfer = client.post(
        "/api/v1/demo/account/transfers",
        json={"trip_id": trip_id, "destination_route_id": 3},
        headers=headers,
    )

    assert transfer.status_code == 201
    assert transfer.json()["origin_route"] == "1"
    assert transfer.json()["destination_route"] == "2"
    assert transfer.json()["additional_charge"] == 0
    assert repeated_transfer.status_code == 409


def test_transfer_rejects_same_or_unknown_route(client: TestClient) -> None:
    headers = auth_headers(client)
    payment = client.post(
        "/api/v1/demo/account/payments",
        json={"route_id": 1, "method": "wallet"},
        headers=headers,
    )
    trip_id = payment.json()["trip_id"]
    same_route = client.post(
        "/api/v1/demo/account/transfers",
        json={"trip_id": trip_id, "destination_route_id": 1},
        headers=headers,
    )
    unknown_route = client.post(
        "/api/v1/demo/account/transfers",
        json={"trip_id": trip_id, "destination_route_id": 999},
        headers=headers,
    )

    assert same_route.status_code == 422
    assert unknown_route.status_code == 404


def test_transfer_rejects_expired_twenty_minute_window(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    headers = auth_headers(client)
    payment = client.post(
        "/api/v1/demo/account/payments",
        json={"route_id": 1, "method": "wallet"},
        headers=headers,
    )
    created_at = services.ahora_servicio()
    monkeypatch.setattr(services, 'ahora_servicio', lambda: created_at + timedelta(minutes=21))

    transfer = client.post(
        "/api/v1/demo/account/transfers",
        json={"trip_id": payment.json()["trip_id"], "destination_route_id": 2},
        headers=headers,
    )

    assert transfer.status_code == 409
    assert "20 minutos" in transfer.json()["detail"]


def test_dynamic_qr_is_signed_renderable_and_charged_once(client: TestClient) -> None:
    passenger = auth_headers(client)
    driver = auth_headers(client, "conductor.demo")
    start_driver(client, driver)
    route_id = next(route["id"] for route in client.get("/api/v1/routes").json() if route["name"] == "24")
    qr = client.post(
        "/api/v1/demo/account/qr",
        json={"route_id": route_id, "validity_minutes": 15},
        headers=passenger,
    )

    assert qr.status_code == 201
    assert qr.json()["status"] == "active"
    assert qr.json()["scannable"] is True
    assert qr.json()["image_data_uri"].startswith("data:image/svg+xml;base64,")
    assert qr.json()["mode"] == "demo"
    scan_data = {"token": qr.json()["token"], "idempotency_key": "scan-request-0001"}
    scan = client.post("/api/v1/driver/qr/validate", json=scan_data, headers=driver)
    retry = client.post("/api/v1/driver/qr/validate", json=scan_data, headers=driver)
    duplicate = client.post(
        "/api/v1/driver/qr/validate",
        json={**scan_data, "idempotency_key": "scan-request-0002"},
        headers=driver,
    )
    assert scan.status_code == 201
    assert retry.status_code == 201
    assert retry.json()["payment_id"] == scan.json()["payment_id"]
    assert duplicate.status_code == 409
    assert client.get("/api/v1/demo/account", headers=passenger).json()["wallet_balance"] == 46700
    assert client.get("/api/v1/driver/shift", headers=driver).json()["qr_total"] == 3300


def test_qr_rejects_invalid_signature_expiration_and_wrong_driver_route(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    passenger = auth_headers(client)
    driver = auth_headers(client, "conductor.demo")
    start_driver(client, driver)
    endpoint_listar_rutas = client.get("/api/v1/routes").json()
    route_1 = next(route["id"] for route in endpoint_listar_rutas if route["name"] == "1")
    route_24 = next(route["id"] for route in endpoint_listar_rutas if route["name"] == "24")

    wrong_route_qr = client.post(
        "/api/v1/demo/account/qr",
        json={"route_id": route_1, "validity_minutes": 15},
        headers=passenger,
    ).json()
    wrong_route = client.post(
        "/api/v1/driver/qr/validate",
        json={"token": wrong_route_qr["token"], "idempotency_key": "scan-wrong-route-001"},
        headers=driver,
    )
    assert wrong_route.status_code == 409

    signed_qr = client.post(
        "/api/v1/demo/account/qr",
        json={"route_id": route_24, "validity_minutes": 15},
        headers=passenger,
    ).json()
    encoded, signature = signed_qr["token"].rsplit(".", 1)
    altered_signature = signature[:-1] + ("0" if signature[-1] != "0" else "1")
    invalid_signature = client.post(
        "/api/v1/driver/qr/validate",
        json={
            "token": f"{encoded}.{altered_signature}",
            "idempotency_key": "scan-invalid-sign-001",
        },
        headers=driver,
    )
    assert invalid_signature.status_code == 422

    expiring_qr = client.post(
        "/api/v1/demo/account/qr",
        json={"route_id": route_24, "validity_minutes": 15},
        headers=passenger,
    ).json()
    now = services.ahora_servicio()
    monkeypatch.setattr(services, 'ahora_servicio', lambda: now + timedelta(minutes=16))
    expired = client.post(
        "/api/v1/driver/qr/validate",
        json={"token": expiring_qr["token"], "idempotency_key": "scan-expired-qr-001"},
        headers=driver,
    )

    assert expired.status_code == 410
