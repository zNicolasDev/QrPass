"""Sesiones firmadas y autorización por rol.

El token es un formato propio: un payload JSON con el identificador de cuenta y
su vencimiento, más una firma HMAC-SHA256 calculada con ``app.state.auth_secret``.
No es un JWT ni depende de librerías de terceros. La clave se fija al arrancar la
aplicación; en desarrollo, si no se configura, es aleatoria y las sesiones dejan
de servir al reiniciar. Los roles se consultan siempre en la base, nunca se
confían al contenido del token.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import obtener_sesion
from app.models import Usuario
from app.seguridad.encoding import decode_base64url, encode_base64url
from app.servicios.usuarios import obtener_usuario_activo, usuario_tiene_rol


DURACION_TOKEN_SEGUNDOS = 60 * 60
bearer_scheme = HTTPBearer(auto_error=False)
SessionDependency = Annotated[Session, Depends(obtener_sesion)]
CredentialsDependency = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(bearer_scheme),
]


def crear_token_acceso(user_id: int, secret: bytes) -> str:
    """Firma el identificador de cuenta y su vencimiento para crear un token.

    El payload se serializa sin espacios para que la firma sea estable y el token
    resulte corto; la comparación se hace en tiempo constante al verificarlo.
    """
    payload = json.dumps(
        {"sub": user_id, "exp": int(time.time()) + DURACION_TOKEN_SEGUNDOS},
        separators=(",", ":"),
    ).encode("utf-8")
    encoded_payload = encode_base64url(payload)
    signature = hmac.new(secret, encoded_payload.encode("ascii"), hashlib.sha256).digest()
    return f"{encoded_payload}.{encode_base64url(signature)}"


def obtener_usuario_autenticado(
    request: Request,
    session: SessionDependency,
    credentials: CredentialsDependency,
) -> Usuario:
    """Verifica la firma, el vencimiento y que la cuenta siga activa.

    Cualquier fallo se traduce al mismo 401 para no revelar si el token estaba
    mal formado, vencido o si la cuenta fue desactivada.
    """
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Autenticación requerida o sesión vencida.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    try:
        payload_part, signature_part = credentials.credentials.split(".")
        secret: bytes = request.app.state.auth_secret

        expected_signature = hmac.new(
            secret,
            payload_part.encode("ascii"),
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(decode_base64url(signature_part), expected_signature):
            raise unauthorized
        payload = json.loads(decode_base64url(payload_part))
        user_id = payload["sub"]
        expires_at = payload["exp"]
        if not isinstance(user_id, int) or expires_at <= time.time():
            raise unauthorized
    except (ValueError, KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
        raise unauthorized from None

    user = obtener_usuario_activo(session, user_id)
    if user is None:
        raise unauthorized
    return user


UsuarioAutenticado = Annotated[Usuario, Depends(obtener_usuario_autenticado)]


def requerir_rol(role_code: str) -> Callable[..., Usuario]:
    """Crea una dependencia que bloquea la operación si falta el rol requerido.

    Se usa como fábrica en los controladores para mantener la comprobación de
    permisos fuera de las reglas de negocio.
    """

    def dependency(user: UsuarioAutenticado) -> Usuario:
        if not usuario_tiene_rol(user, role_code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tu cuenta no tiene el rol requerido para esta operación.",
            )
        return user

    return dependency
