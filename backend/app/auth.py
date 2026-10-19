from __future__ import annotations
# Este módulo crea y comprueba sesiónes firmadas y aplica los permisos por rol.

import base64
import hashlib
import hmac
import json
import time
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import obtener_sesion
from app.models import Usuario
from app.services import obtener_usuario_activo, usuario_tiene_rol


DURACION_TOKEN_SEGUNDOS = 60 * 60
bearer_scheme = HTTPBearer(auto_error=False)
SessionDependency = Annotated[Session, Depends(obtener_sesion)]
CredentialsDependency = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(bearer_scheme),
]


# Firma el identificador de cuenta y su vencimiento para crear un token.
def crear_token_acceso(user_id: int, secret: bytes) -> str:
    # La sesión no guarda una copia del perfil: el token solo identifica a la
    # cuenta y su vencimiento; al usarlo volvemos a comprobarla en la base.
    # El contenido no es secreto: se firma para que nadie pueda cambiar su ID
    # o vencimiento sin que el servidor detecte la modificación.
    payload = json.dumps(
        {"sub": user_id, "exp": int(time.time()) + DURACION_TOKEN_SEGUNDOS},
        separators=(",", ":"),
    ).encode("utf-8")
    encoded_payload = _encode(payload)
    signature = hmac.new(secret, encoded_payload.encode("ascii"), hashlib.sha256).digest()
    return f"{encoded_payload}.{_encode(signature)}"


# Verifica el token y busca la cuenta activa que lo presenta.
def obtener_usuario_autenticado(
    request: Request,
    session: SessionDependency,
    credentials: CredentialsDependency,
) -> Usuario:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Autenticación requerida o sesión vencida.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    try:
        # El token tiene dos partes: el contenido codificado y su firma.
        payload_part, signature_part = credentials.credentials.split(".")
        secret: bytes = request.app.state.auth_secret

        # Se vuelve a calcular la firma y se compara de forma segura para evitar
        # aceptar un token alterado.
        expected_signature = hmac.new(
            secret,
            payload_part.encode("ascii"),
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(_decode(signature_part), expected_signature):
            raise unauthorized
        # Solo después de validar la firma se confía en el identificador y la fecha.
        payload = json.loads(_decode(payload_part))
        user_id = payload["sub"]
        expires_at = payload["exp"]
        if not isinstance(user_id, int) or expires_at <= time.time():
            raise unauthorized
    except (ValueError, KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
        raise unauthorized from None

    # La consulta de cuenta y roles vive en el servicio, no en esta dependencia HTTP.
    user = obtener_usuario_activo(session, user_id)
    if user is None:
        raise unauthorized
    return user


UsuarioAutenticado = Annotated[Usuario, Depends(obtener_usuario_autenticado)]


# Crea una dependencia que bloquea la operación si falta el rol requerido.
def requerir_rol(role_code: str) -> Callable[..., Usuario]:
    # FastAPI usa esta función para crear dependencias específicas, por ejemplo
    # una que solo permita entrar a las operaciones del conductor.
    def dependency(user: UsuarioAutenticado) -> Usuario:
        # Ocultar una opción en pantalla mejora la experiencia, pero el permiso
        # se decide aquí porque cualquier cliente puede llamar la API directamente.
        if not usuario_tiene_rol(user, role_code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tu cuenta no tiene el rol requerido para esta operación.",
            )
        return user

    return dependency


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
