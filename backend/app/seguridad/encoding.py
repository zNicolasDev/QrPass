"""Codificación base64url sin relleno, compartida por tokens y hashes.

Las sesiones y las contraseñas necesitan exactamente la misma representación:
si un módulo cambiara el formato, los tokens emitidos y los hashes ya guardados
dejarían de verificarse. Mantener una sola implementación evita esa divergencia.
"""

from __future__ import annotations

import base64


def encode_base64url(value: bytes) -> str:
    """Codifica bytes en base64url sin el relleno ``=`` final."""
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def decode_base64url(value: str) -> bytes:
    """Invierte :func:`encode_base64url` restaurando el relleno omitido."""
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
