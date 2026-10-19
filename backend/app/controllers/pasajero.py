from __future__ import annotations
# Este controlador recibe las consultas y operaciónes de la cuenta pasajera.
import logging
from typing import Annotated
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi import status
from sqlalchemy.orm import Session
from app.auth import UsuarioAutenticado
from app.database import obtener_sesion
from app.dtos import CuentaRespuesta
from app.dtos import CrearPagoSolicitud
from app.dtos import HistorialPagosRespuesta
from app.dtos import ReciboPago
from app.dtos import CrearCodigoQrSolicitud
from app.dtos import CodigoQrRespuesta
from app.dtos import CrearRecargaSolicitud
from app.dtos import ReciboRecarga
from app.dtos import CrearTransbordoSolicitud
from app.dtos import TransbordoRespuesta
from app.dtos import ViajeRespuesta
from app.models import Viaje
from app.services import crear_pago
from app.services import crear_codigo_qr
from app.services import crear_recarga
from app.services import crear_transbordo
from app.services import obtener_viaje
from app.services import listar_pagos
from app.services import listar_viajes
from app.services import crear_imagen_qr




SessionDependency = Annotated[Session, Depends(obtener_sesion)]
logger = logging.getLogger(__name__)
demo_router = APIRouter(prefix="/demo/account", tags=["Demostraci?n"])
router = APIRouter()

# El servicio entrega un viaje con sus relaciones; esta función lo convierte
# en el DTO que verá la persona en el historial.
def _representar_viaje(trip: Viaje) -> ViajeRespuesta:
    return ViajeRespuesta(
        viaje_id=trip.id,
        ruta_id=trip.ruta_id,
        nombre_ruta=trip.ruta.nombre,
        pago_id=trip.pago_id,
        medio=trip.pago.medio,
        tipo_movimiento=trip.pago.tipo_movimiento,
        monto=trip.pago.monto,
        estado=trip.pago.estado,
        creado_en=trip.creado_en,
        transferido_a=trip.transbordo_origen.ruta_destino.nombre if trip.transbordo_origen else None,
    )

# Devuelve el saldo de la cuenta autenticada.
@demo_router.get("", response_model=CuentaRespuesta, summary="Consultar la cuenta autenticada")
def endpoint_cuenta_demo(user: UsuarioAutenticado) -> CuentaRespuesta:
    # El usuario ya fue autenticado por la dependencia; solo se muestra su saldo.
    return CuentaRespuesta(usuario_id=user.id, nombres=user.nombres, saldo_billetera=user.saldo_billetera)

# Solicita un QR firmado y prepara su imagen para mostrarla.
@demo_router.post("/qr", response_model=CodigoQrRespuesta, status_code=status.HTTP_201_CREATED)
def endpoint_generar_qr_demo(
    payload: CrearCodigoQrSolicitud,
    request: Request,
    user: UsuarioAutenticado,
    session: SessionDependency,
) -> CodigoQrRespuesta:
    # El servicio valida saldo, ruta y tarifa, y guarda un QR temporal.
    qr_code = crear_codigo_qr(
        session, user, payload.ruta_id, payload.vigencia_minutos, request.app.state.auth_secret,
    )
    # La imagen SVG se genera desde el token guardado para facilitar el escaneo.
    return CodigoQrRespuesta(
        codigo_qr_id=qr_code.id,
        token=qr_code.token,
        estado=qr_code.estado,
        creado_en=qr_code.creado_en,
        vence_en=qr_code.vence_en,
        imagen_data_uri=crear_imagen_qr(qr_code.token),
    )

# Presenta pagos y recargas de la cuenta autenticada.
@router.get("/payments/history", response_model=list[HistorialPagosRespuesta], tags=["Pagos"], summary="Consultar el historial unificado de pagos")
def endpoint_historial_pagos(user: UsuarioAutenticado, session: SessionDependency) -> list[HistorialPagosRespuesta]:
    # La consulta pertenece al servicio. El controlador arma un DTO por pago;
    # una recarga no tiene viaje, por eso sus datos de viaje quedan vacíos.
    return [
        HistorialPagosRespuesta(
            pago_id=payment.id,
            tipo_movimiento=payment.tipo_movimiento,
            medio=payment.medio,
            monto=payment.monto,
            saldo_anterior=payment.saldo_anterior,
            saldo_posterior=payment.saldo_posterior,
            estado=payment.estado,
            creado_en=payment.creado_en,
            viaje_id=payment.viaje.id if payment.viaje else None,
            ruta_id=payment.viaje.ruta_id if payment.viaje else None,
            nombre_ruta=payment.viaje.ruta.nombre if payment.viaje else None,
        )
        for payment in listar_pagos(session, user)
    ]

# Presenta los viajes del pasajero.
@router.get("/trips", response_model=list[ViajeRespuesta], tags=["Viajes"], summary="Consultar el historial de viajes")
def endpoint_historial_viajes(user: UsuarioAutenticado, session: SessionDependency) -> list[ViajeRespuesta]:
    # Cada viaje se convierte por la misma función para mantener una respuesta uniforme.
    return [_representar_viaje(trip) for trip in listar_viajes(session, user)]

# Busca un viaje propio y devuelve su detalle.
@router.get("/trips/{trip_id}", response_model=ViajeRespuesta, tags=["Viajes"], summary="Consultar el detalle de un viaje")
def endpoint_detalle_viaje(trip_id: int, user: UsuarioAutenticado, session: SessionDependency) -> ViajeRespuesta:
    # El servicio comprueba que el viaje exista y pertenezca a esta cuenta.
    return _representar_viaje(obtener_viaje(session, user, trip_id))

@demo_router.get("/trips", response_model=list[ViajeRespuesta], summary="Consultar el historial de prueba")
def endpoint_historial_viajes_demo(user: UsuarioAutenticado, session: SessionDependency) -> list[ViajeRespuesta]:
    # Esta ruta de demostración usa el mismo historial del usuario autenticado.
    return [_representar_viaje(trip) for trip in listar_viajes(session, user)]

# Solicita al servicio cobrar la tarifa y crear el viaje.
@demo_router.post("/payments", response_model=ReciboPago, status_code=status.HTTP_201_CREATED)
def endpoint_pagar_viaje(payload: CrearPagoSolicitud, user: UsuarioAutenticado, session: SessionDependency) -> ReciboPago:
    # El servicio aplica las reglas del cobro y crea el pago y el viaje.
    payment, trip, wallet_balance = crear_pago(session, user, payload)
    # El recibo resume lo que se confirmó en la operación.
    return ReciboPago(
        pago_id=payment.id,
        viaje_id=trip.id,
        ruta_id=trip.ruta_id,
        nombre_ruta=trip.ruta.nombre,
        medio=payment.medio,
        tipo_tarjeta=payload.tipo_tarjeta.value if payload.tipo_tarjeta else None,
        tipo_movimiento=payment.tipo_movimiento,
        monto=payment.monto,
        saldo_billetera=wallet_balance,
        estado=payment.estado,
        creado_en=payment.creado_en,
    )

# Solicita al servicio acreditar una recarga.
@demo_router.post("/top-ups", response_model=ReciboRecarga, status_code=status.HTTP_201_CREATED)
def endpoint_recargar_billetera(payload: CrearRecargaSolicitud, user: UsuarioAutenticado, session: SessionDependency) -> ReciboRecarga:
    # El servicio valida y acredita el saldo; el controlador prepara el recibo.
    payment = crear_recarga(session, user, payload)
    return ReciboRecarga(
        pago_id=payment.id,
        monto=payment.monto,
        saldo_billetera=payment.saldo_posterior,
        estado=payment.estado,
        creado_en=payment.creado_en,
    )

# Solicita al servicio cambiar la ruta de un viaje elegible.
@demo_router.post("/transfers", response_model=TransbordoRespuesta, status_code=status.HTTP_201_CREATED)
def endpoint_transferir_viaje(payload: CrearTransbordoSolicitud, user: UsuarioAutenticado, session: SessionDependency) -> TransbordoRespuesta:
    # El servicio valida tiempo, propiedad y rutas antes de crear el transbordo.
    transfer = crear_transbordo(session, user, payload)
    return TransbordoRespuesta(
        transbordo_id=transfer.id,
        viaje_origen_id=transfer.viaje_origen_id,
        ruta_origen=transfer.viaje_origen.ruta.nombre,
        ruta_destino_id=transfer.ruta_destino_id,
        ruta_destino=transfer.ruta_destino.nombre,
        creado_en=transfer.creado_en,
    )
