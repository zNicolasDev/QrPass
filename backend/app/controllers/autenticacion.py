from __future__ import annotations
# Este controlador recibe registro e inicio de sesión y convierte el resultado en respuestas HTTP.
from typing import Annotated
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from sqlalchemy.orm import Session
from app.auth import DURACION_TOKEN_SEGUNDOS
from app.auth import UsuarioAutenticado
from app.auth import crear_token_acceso
from app.database import obtener_sesion
from app.dtos import UsuarioAutenticadoRespuesta
from app.dtos import InicioSesionSolicitud
from app.dtos import InicioSesionRespuesta
from app.dtos import RegistroPasajeroSolicitud
from app.models import Usuario
from app.services import autenticar_usuario
from app.services import registrar_pasajero




SessionDependency = Annotated[Session, Depends(obtener_sesion)]
# Este router agrupa las direcciones web relacionadas con registro e inicio de sesión.
auth_router = APIRouter(prefix="/auth", tags=["Autenticaci?n"])

def _representar_usuario_autenticado(user: Usuario) -> UsuarioAutenticadoRespuesta:
    # El token y el perfil necesitan un nombre de usuario para identificar la sesión.
    if user.nombre_usuario is None:
        raise HTTPException(status_code=409, detail="La cuenta no tiene un usuario de inicio de sesión.")

    # El modelo tiene campos internos; el DTO devuelve solo los datos públicos.
    return UsuarioAutenticadoRespuesta(
        usuario_id=user.id,
        nombre_usuario=user.nombre_usuario,
        correo=user.correo,
        nombres=user.nombres,
        roles=sorted(user_role.rol.codigo for user_role in user.roles),
    )

# Valida que el correo sea único, crea la cuenta como pasajera y devuelve su identidad.
@auth_router.post(
    "/register",
    response_model=UsuarioAutenticadoRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una cuenta pasajera",
)
def endpoint_registrar_pasajero(payload: RegistroPasajeroSolicitud, session: SessionDependency) -> UsuarioAutenticadoRespuesta:
    # El DTO valida el formato. El servicio aplica reglas y guarda la cuenta;
    # el controlador convierte el resultado al formato público de respuesta.
    user = registrar_pasajero(session, str(payload.nombres), str(payload.correo), payload.contrasena)
    return _representar_usuario_autenticado(user)

# Comprueba la contraseña y entrega un token de acceso temporal.
@auth_router.post("/login", response_model=InicioSesionRespuesta, summary="Iniciar sesión")
def endpoint_iniciar_sesion(payload: InicioSesionSolicitud, request: Request, session: SessionDependency) -> InicioSesionRespuesta:
    # El servicio busca la cuenta activa y comprueba la contraseña antes de
    # permitir que esta capa cree un token de sesión.
    user = autenticar_usuario(session, payload.nombre_usuario, payload.contrasena)
    token = crear_token_acceso(user.id, request.app.state.auth_secret)

    # El frontend recibe el token, el perfil y el tiempo hasta su vencimiento.
    return InicioSesionRespuesta(
        token_acceso=token,
        vence_en_segundos=DURACION_TOKEN_SEGUNDOS,
        usuario=_representar_usuario_autenticado(user),
    )

# Devuelve la identidad y los roles asociados al token actual.
@auth_router.get("/me", response_model=UsuarioAutenticadoRespuesta, summary="Consultar usuario y roles autenticados")
def endpoint_usuario_actual(user: UsuarioAutenticado) -> UsuarioAutenticadoRespuesta:
    # FastAPI obtiene y valida la cuenta desde el token antes de entrar aquí.
    return _representar_usuario_autenticado(user)
