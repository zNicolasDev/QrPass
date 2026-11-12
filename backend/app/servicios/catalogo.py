from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Ruta, Tarifa


RUTA_CATALOGO = Path(__file__).resolve().parents[1] / "datos_maestros" / "rutas_tarifas.json"


def cargar_catalogo(path: Path = RUTA_CATALOGO) -> dict[str, object]:
    # Lee el catálogo maestro versionado junto a la aplicación.
    with path.open(encoding="utf-8") as archivo:
        return json.load(archivo)


def _asegurar_ruta(session: Session, nombre: str) -> tuple[Ruta, bool]:
    ruta = session.scalar(select(Ruta).where(Ruta.nombre == nombre))
    if ruta is None:
        ruta = Ruta(nombre=nombre, activa=True)
        session.add(ruta)
        session.flush()
        return ruta, True
    if not ruta.activa:
        ruta.activa = True
    return ruta, False


def _asegurar_tarifa(
    session: Session,
    ruta_id: int,
    tipo_dia: str,
    monto: int,
    destino: str | None = None,
) -> tuple[Tarifa, bool]:
    tarifa = session.scalar(
        select(Tarifa).where(
            Tarifa.ruta_id == ruta_id,
            Tarifa.tipo_dia == tipo_dia,
            Tarifa.destino == destino,
        )
    )
    if tarifa is None:
        tarifa = Tarifa(
            ruta_id=ruta_id,
            tipo_dia=tipo_dia,
            destino=destino,
            monto=monto,
            activa=True,
        )
        session.add(tarifa)
        return tarifa, True
    tarifa.monto = monto
    tarifa.activa = True
    return tarifa, False


def importar_catalogo(session: Session, path: Path = RUTA_CATALOGO) -> dict[str, int]:
    # Carga idempotente: puede ejecutarse varias veces sin duplicar rutas ni tarifas.
    data = cargar_catalogo(path)
    rutas = data.get("rutas", [])
    tarifas_ordinarias = data.get("tarifas_ordinarias", {})
    tarifas_por_destino = data.get("tarifas_por_destino", {})

    if not isinstance(rutas, list) or not isinstance(tarifas_ordinarias, dict):
        raise ValueError("El catálogo maestro no tiene el formato esperado.")
    if not isinstance(tarifas_por_destino, dict):
        raise ValueError("El catálogo maestro no tiene el formato esperado.")

    resumen = {
        "rutas_creadas": 0,
        "rutas_actualizadas": 0,
        "tarifas_creadas": 0,
        "tarifas_actualizadas": 0,
    }

    for nombre in rutas:
        ruta, creada = _asegurar_ruta(session, str(nombre))
        if creada:
            resumen["rutas_creadas"] += 1
        else:
            resumen["rutas_actualizadas"] += 1

        for tipo_dia, monto in tarifas_ordinarias.items():
            _, tarifa_creada = _asegurar_tarifa(
                session, ruta.id, str(tipo_dia), int(monto), destino=None
            )
            clave = "tarifas_creadas" if tarifa_creada else "tarifas_actualizadas"
            resumen[clave] += 1

        destinos = tarifas_por_destino.get(str(nombre), {})
        if not isinstance(destinos, dict):
            raise ValueError(f"Las tarifas por destino de la ruta {nombre} no son válidas.")
        for destino, montos in destinos.items():
            if not isinstance(montos, dict):
                raise ValueError(f"La tarifa del destino {destino} no es válida.")
            for tipo_dia, monto in montos.items():
                _, tarifa_creada = _asegurar_tarifa(
                    session, ruta.id, str(tipo_dia), int(monto), destino=str(destino)
                )
                clave = "tarifas_creadas" if tarifa_creada else "tarifas_actualizadas"
                resumen[clave] += 1

    session.commit()
    return resumen
