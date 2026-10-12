from typing import Annotated, Literal

from pydantic import EmailStr, Field

from app.dtos.base import EsquemaBase


class InicioSesionSolicitud(EsquemaBase):
    # Entrada del login; los alias mantienen el JSON en inglés y el código en español.
    nombre_usuario: Annotated[str, Field(min_length=3, max_length=254, validation_alias="username", serialization_alias="username")]
    contrasena: Annotated[str, Field(min_length=1, max_length=256, validation_alias="password", serialization_alias="password")]


class RegistroPasajeroSolicitud(EsquemaBase):
    # Entrada del registro: Pydantic comprueba formato, longitudes y consentimiento.
    nombres: Annotated[str, Field(min_length=2, max_length=120, validation_alias="names", serialization_alias="names")]
    correo: EmailStr = Field(validation_alias="email", serialization_alias="email")
    contrasena: Annotated[str, Field(min_length=12, max_length=256, validation_alias="password", serialization_alias="password")]
    # Literal[True] obliga a que el cliente envíe true, no false ni otro valor.
    consentimiento_privacidad: Literal[True] = Field(validation_alias="privacy_consent", serialization_alias="privacy_consent")


class UsuarioAutenticadoRespuesta(EsquemaBase):
    # Perfil público de sesión; no incluye la contraseña ni su hash.
    usuario_id: int = Field(validation_alias="user_id", serialization_alias="user_id")
    nombre_usuario: str = Field(validation_alias="username", serialization_alias="username")
    correo: EmailStr | None = Field(default=None, validation_alias="email", serialization_alias="email")
    nombres: str = Field(validation_alias="names", serialization_alias="names")
    roles: list[str]
    modo: str = Field(default="demo", validation_alias="mode", serialization_alias="mode")


class InicioSesionRespuesta(EsquemaBase):
    # Respuesta de login: token, vencimiento y perfil autenticado.
    token_acceso: str = Field(validation_alias="access_token", serialization_alias="access_token")
    tipo_token: str = Field(default="bearer", validation_alias="token_type", serialization_alias="token_type")
    vence_en_segundos: int = Field(validation_alias="expires_in", serialization_alias="expires_in")
    usuario: UsuarioAutenticadoRespuesta = Field(validation_alias="user", serialization_alias="user")
