from __future__ import annotations

import secrets
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import Conductor, Rol, RolUsuario, Usuario
from app.seguridad.passwords import crear_hash_contrasena, verificar_contrasena
from app.servicios.comun import ErrorDominio, ahora_servicio


ROLES_PASAJERO = ("PASSENGER",)
ROLES_CONDUCTOR = ("PASSENGER", "DRIVER")
ROLES_ADMINISTRADOR = ("PASSENGER", "ADMIN")


def _obtener_rol(session: Session, codigo: str) -> Rol:
    rol = session.scalar(select(Rol).where(Rol.codigo == codigo))
    if rol is None:
        raise ErrorDominio(503, "Los roles del sistema no están inicializados.")
    return rol


def _crear_usuario(
    session: Session,
    names: str,
    email: str,
    password: str,
    roles: tuple[str, ...],
) -> Usuario:
    # Punto único para crear cuentas; cada perfil decide qué roles recibe.
    normalized_email = email.strip().lower()
    if session.scalar(select(Usuario.id).where(Usuario.correo == normalized_email)) is not None:
        raise ErrorDominio(409, "Ya existe una cuenta con ese correo.")
    roles_sistema = [_obtener_rol(session, codigo) for codigo in roles]
    user = Usuario(
        nombres=" ".join(names.split()),
        nombre_usuario=normalized_email,
        correo=normalized_email,
        hash_contrasena=crear_hash_contrasena(password),
        consentimiento_privacidad_en=ahora_servicio(),
        numero_documento=f"QRPASS-{secrets.token_hex(12)}",
        saldo_billetera=0,
        estado="active",
    )
    session.add(user)
    session.flush()
    user.roles.extend(RolUsuario(rol=rol) for rol in roles_sistema)
    session.flush()
    return user


def registrar_pasajero(session: Session, names: str, email: str, password: str) -> Usuario:
    user = _crear_usuario(session, names, email, password, ROLES_PASAJERO)
    session.commit()
    session.refresh(user)
    return user


def crear_conductor(
    session: Session,
    names: str,
    email: str,
    password: str,
    license_number: str,
) -> Usuario:
    licencia = license_number.strip()
    if session.scalar(select(Conductor.usuario_id).where(Conductor.numero_licencia == licencia)) is not None:
        raise ErrorDominio(409, "Ya existe un conductor con esa licencia.")
    user = _crear_usuario(session, names, email, password, ROLES_CONDUCTOR)
    session.add(Conductor(usuario_id=user.id, numero_licencia=licencia))
    session.commit()
    session.refresh(user)
    return user


def crear_administrador(session: Session, names: str, email: str, password: str) -> Usuario:
    user = _crear_usuario(session, names, email, password, ROLES_ADMINISTRADOR)
    session.commit()
    session.refresh(user)
    return user


def autenticar_usuario(session: Session, username: str, password: str) -> Usuario:
    user = session.execute(
        select(Usuario)
        .options(joinedload(Usuario.roles).joinedload(RolUsuario.rol))
        .where(Usuario.nombre_usuario == username, Usuario.estado == "active")
    ).unique().scalar_one_or_none()
    if user is None or not verificar_contrasena(password, user.hash_contrasena):
        raise ErrorDominio(401, "Usuario o contraseña incorrectos.")
    return user


def obtener_usuario_activo(session: Session, user_id: int) -> Usuario | None:
    return session.scalar(
        select(Usuario)
        .options(selectinload(Usuario.roles).selectinload(RolUsuario.rol))
        .where(Usuario.id == user_id, Usuario.estado == "active")
    )


def usuario_tiene_rol(user: Usuario, role_code: str) -> bool:
    return any(user_role.rol.codigo == role_code for user_role in user.roles)


def obtener_perfil_conductor(session: Session, user: Usuario) -> Conductor | None:
    return session.get(Conductor, user.id)


def obtener_datos_asignacion_conductor(session: Session, user: Usuario) -> tuple[Conductor | None, Any]:
    from app.servicios.turnos import _asegurar_asignacion_conductor
    # Si el conductor cerró su turno, se restituye su asignación para que pueda iniciar otro.
    return session.get(Conductor, user.id), _asegurar_asignacion_conductor(session, user)
