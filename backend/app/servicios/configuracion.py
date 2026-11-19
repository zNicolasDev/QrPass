from __future__ import annotations

# Catálogos constantes de la aplicación, persistidos en la base de datos.
# El repositorio no contiene archivos con datos semilla.

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Configuracion, Rol

CLAVE_ROLES = "roles"
CLAVE_PERFILES = "perfiles_roles"
CLAVE_CATALOGO = "catalogo"


def guardar_configuracion(session: Session, clave: str, valor: Any) -> None:
    fila = session.get(Configuracion, clave)
    contenido = json.dumps(valor, ensure_ascii=False)
    if fila is None:
        session.add(Configuracion(clave=clave, valor=contenido))
    else:
        fila.valor = contenido


def obtener_configuracion(session: Session, clave: str, default: Any = None) -> Any:
    fila = session.get(Configuracion, clave)
    if fila is None:
        return default
    return json.loads(fila.valor)


def sembrar_configuracion(session: Session, catalogo: dict[str, Any]) -> None:
    # Una sola entrada por bloque; reemplaza cualquier siembra anterior.
    guardar_configuracion(session, CLAVE_ROLES, catalogo["roles"])
    guardar_configuracion(session, CLAVE_PERFILES, catalogo["perfiles_roles"])
    guardar_configuracion(
        session,
        CLAVE_CATALOGO,
        {
            "rutas": catalogo["rutas"],
            "tarifas_ordinarias": catalogo["tarifas_ordinarias"],
            "tarifas_por_destino": catalogo["tarifas_por_destino"],
        },
    )
    # Las sesiones usan autoflush=False, así que las filas nuevas deben
    # escribirse antes de que otra consulta intente leerlas.
    session.flush()


def roles_iniciales(session: Session) -> list[tuple[str, str]]:
    roles = obtener_configuracion(session, CLAVE_ROLES, [])
    return [(rol["code"], rol["name"]) for rol in roles]


def roles_del_perfil(session: Session, perfil: str) -> tuple[str, ...]:
    perfiles = obtener_configuracion(session, CLAVE_PERFILES, {})
    return tuple(perfiles[perfil])


def asegurar_roles(session: Session) -> None:
    for codigo, nombre in roles_iniciales(session):
        if session.scalar(select(Rol).where(Rol.codigo == codigo)) is None:
            session.add(Rol(codigo=codigo, nombre=nombre))
    session.flush()


def catalogo_rutas_tarifas(session: Session) -> dict[str, Any] | None:
    return obtener_configuracion(session, CLAVE_CATALOGO)
