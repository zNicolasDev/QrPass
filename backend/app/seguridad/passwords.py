"""Hash y verificación de contraseñas con PBKDF2-HMAC-SHA256.

Nunca se guarda la contraseña original. El formato guardado es
``pbkdf2_sha256$iteraciones$salt$digest``; las iteraciones viajan con el hash
para poder aumentar el coste en el futuro sin invalidar registros antiguos.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

from app.seguridad.encoding import decode_base64url, encode_base64url


PASSWORD_HASH_ITERATIONS = 310_000


def crear_hash_contrasena(password: str) -> str:
    """Genera una sal aleatoria y devuelve el hash, no la contraseña original."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_HASH_ITERATIONS,
    )
    return (
        f"pbkdf2_sha256${PASSWORD_HASH_ITERATIONS}$"
        f"{encode_base64url(salt)}${encode_base64url(digest)}"
    )


def verificar_contrasena(password: str, encoded_hash: str | None) -> bool:
    """Compara la contraseña recibida con el hash guardado en tiempo constante.

    El rango de iteraciones se acota para rechazar valores corruptos o
    manipulados antes de dedicar tiempo a calcular el PBKDF2.
    """
    if encoded_hash is None:
        return False
    try:
        algorithm, iterations_text, salt_text, digest_text = encoded_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_text)
        if not 100_000 <= iterations <= 2_000_000:
            return False
        salt = decode_base64url(salt_text)
        expected = decode_base64url(digest_text)
    except (ValueError, TypeError):
        return False

    actual = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(actual, expected)
