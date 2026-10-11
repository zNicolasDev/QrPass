from __future__ import annotations

import base64
import hashlib
import hmac
import secrets


PASSWORD_HASH_ITERATIONS = 310_000


def crear_hash_contrasena(password: str) -> str:
    # Cada cuenta recibe su propio azar; guardar solo el resultado evita que
    # una filtración de la base revele contraseñas listas para reutilizar.
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_HASH_ITERATIONS,
    )
    return f"pbkdf2_sha256${PASSWORD_HASH_ITERATIONS}${_encode(salt)}${_encode(digest)}"


def verificar_contrasena(password: str, encoded_hash: str | None) -> bool:
    if encoded_hash is None:
        return False
    try:
        algorithm, iterations_text, salt_text, digest_text = encoded_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_text)
        if not 100_000 <= iterations <= 2_000_000:
            return False
        salt = _decode(salt_text)
        expected = _decode(digest_text)
    except (ValueError, TypeError):
        return False

    actual = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(actual, expected)


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
