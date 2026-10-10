from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from aplicacion.base_datos import get_session
from aplicacion.modelos import User, UserRole
from aplicacion.contrasenas import verify_password


ACCESS_TOKEN_SECONDS = 60 * 60
bearer_scheme = HTTPBearer(auto_error=False)
SessionDependency = Annotated[Session, Depends(get_session)]
CredentialsDependency = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(bearer_scheme),
]


def create_access_token(user_id: int, secret: bytes) -> str:
    # La sesión no guarda una copia del perfil: el token solo identifica a la
    # cuenta y su vencimiento; al usarlo volvemos a comprobarla en la base.
    payload = json.dumps(
        {"sub": user_id, "exp": int(time.time()) + ACCESS_TOKEN_SECONDS},
        separators=(",", ":"),
    ).encode("utf-8")
    encoded_payload = _encode(payload)
    signature = hmac.new(secret, encoded_payload.encode("ascii"), hashlib.sha256).digest()
    return f"{encoded_payload}.{_encode(signature)}"


def get_authenticated_user(
    request: Request,
    session: SessionDependency,
    credentials: CredentialsDependency,
) -> User:
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
        if not hmac.compare_digest(_decode(signature_part), expected_signature):
            raise unauthorized
        payload = json.loads(_decode(payload_part))
        user_id = payload["sub"]
        expires_at = payload["exp"]
        if not isinstance(user_id, int) or expires_at <= time.time():
            raise unauthorized
    except (ValueError, KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
        raise unauthorized from None

    user = session.scalar(
        select(User)
        .options(selectinload(User.roles).selectinload(UserRole.role))
        .where(User.id == user_id, User.status == "active")
    )
    if user is None:
        raise unauthorized
    return user


AuthenticatedUser = Annotated[User, Depends(get_authenticated_user)]


def require_role(role_code: str) -> Callable[..., User]:
    def dependency(user: AuthenticatedUser) -> User:
        # Ocultar una opción en pantalla mejora la experiencia, pero el permiso
        # se decide aquí porque cualquier cliente puede llamar la API directamente.
        if not any(user_role.role.code == role_code for user_role in user.roles):
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
