from __future__ import annotations
# Utilidades comunes y excepciones de dominio compartidas por todos los servicios.

import sys
from datetime import date, datetime, timedelta, timezone
from typing import TypedDict, Any
from zoneinfo import ZoneInfo

import holidays

IBAGUE_TIMEZONE = ZoneInfo("America/Bogota")


class ResumenMovimientoTurno(TypedDict):
    payment_id: int
    route_name: str
    method: str
    amount: int
    created_at: datetime


class ResumenTurnoConductor(TypedDict):
    shift: Any
    cash: int
    qr: int
    card: int
    payment_count: int
    entries: list[ResumenMovimientoTurno]


class ErrorDominio(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def _default_ahora() -> datetime:
    return datetime.now(timezone.utc)


def _default_fecha() -> date:
    return datetime.now(IBAGUE_TIMEZONE).date()


def ahora_servicio() -> datetime:
    # Permite que las pruebas reemplacen la hora en cualquiera de los módulos
    # habituales (app.servicios, app.servicios.comun).
    for modname in ("app.servicios", "app.servicios.comun"):
        mod = sys.modules.get(modname)
        if mod is None:
            continue
        fn = getattr(mod, "ahora_servicio", None)
        if fn is None or fn is ahora_servicio:
            continue
        if fn is _default_ahora:
            continue
        try:
            return fn()
        except Exception:
            continue
    return _default_ahora()


def fecha_servicio() -> date:
    for modname in ("app.servicios", "app.servicios.comun"):
        mod = sys.modules.get(modname)
        if mod is None:
            continue
        fn = getattr(mod, "fecha_servicio", None)
        if fn is None or fn is fecha_servicio:
            continue
        if fn is _default_fecha:
            continue
        try:
            return fn()
        except Exception:
            continue
    return _default_fecha()


def tipo_dia(day: date) -> str:
    return "weekend" if day.weekday() == 6 or day in holidays.country_holidays("CO", years=day.year) else "weekday"