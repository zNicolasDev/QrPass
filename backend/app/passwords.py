from __future__ import annotations
# Este módulo convierte contraseñas en hashes seguros y comprueba las contraseñas al iniciar sesión.

import base64
import hashlib
import hmac
import secrets


PASSWORD_HASH_ITERATIONS = 310_000


# Genera una sal aleatoria y guarda un hash, no la contraseña original.
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


# Compara la contraseña ingresada con el hash guardado.
def verificar_contrasena(password: str, encoded_hash: str | None) -> bool:
    # Una cuenta demo antigua puede no tener hash; nunca se acepta una clave
    # en texto plano como reemplazo.
    if encoded_hash is None:
        return False
    try:
        # Se separan algoritmo, costo, sal y resultado guardados al registrar.
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

    # Se repite el cálculo con la clave ingresada y la sal guardada.
    actual = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    # La comparación evita filtrar información por el tiempo que toma comparar.
    return hmac.compare_digest(actual, expected)


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
