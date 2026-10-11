from __future__ import annotations

import datetime
import logging
from datetime import date
import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.auth import (
    DURACION_TOKEN_SEGUNDOS,
    UsuarioAutenticado,
    crear_token_acceso,
    requerir_rol,
    verificar_contrasena,
)
from app.database import obtener_sesion
from app.dtos import (
    CuentaRespuesta,
    UsuarioAutenticadoRespuesta,
    AsignacionConductorRespuesta,
    MovimientoTurnoRespuesta,
    CierreTurnoSolicitud,
    PagoConductorSolicitud,
    ValidacionQrConductorSolicitud,
    TurnoConductorRespuesta,
    TarifaRespuesta,
    EstadoServicioRespuesta,
    InicioSesionSolicitud,
    InicioSesionRespuesta,
    CrearPagoSolicitud,
    HistorialPagosRespuesta,
    ReciboPago,
    RegistroPasajeroSolicitud,
    CrearCodigoQrSolicitud,
    CodigoQrRespuesta,
    RutaRespuesta,
    CierreTurnoRespuesta,
    CrearRecargaSolicitud,
    ReciboRecarga,
    CrearTransbordoSolicitud,
    TransbordoRespuesta,
    ViajeRespuesta,
)
from app.models import Conductor, Rol, Viaje, Usuario, RolUsuario
from app.services import (
    obtener_turno_activo_conductor,
    obtener_asignacion_conductor,
    cerrar_turno_conductor,
    crear_pago,
    crear_codigo_qr,
    crear_recarga,
    crear_transbordo,
    consultar_historial_turnos,
    resumir_turno_conductor,
    ResumenTurnoConductor,
    obtener_tarifa_vigente,
    obtener_viaje,
    listar_pagos,
    listar_rutas,
    listar_viajes,
    crear_imagen_qr,
    registrar_pago_conductor,
    validar_y_canjear_qr,
)
from app.passwords import crear_hash_contrasena


# Las rutas son la recepción de la API: traducen lo que llega y delegan las
# decisiones de negocio en servicios.py para que no haya reglas distintas por endpoint.
SessionDependency = Annotated[Session, Depends(obtener_sesion)]
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1")
demo_router = APIRouter(prefix="/demo/account", tags=["Demostración"])
auth_router = APIRouter(prefix="/auth", tags=["Autenticación"])
driver_router = APIRouter(prefix="/driver", tags=["Conductor"])


@router.get("/health", response_model=EstadoServicioRespuesta, tags=["Sistema"])
def endpoint_estado_salud() -> EstadoServicioRespuesta:
    return EstadoServicioRespuesta(estado="ok", servicio="qrpass-api", modo="demo")


@router.get("/ready", response_model=EstadoServicioRespuesta, tags=["Sistema"], summary="Verificar disponibilidad de la base de datos")
def endpoint_verificar_disponibilidad(request: Request) -> EstadoServicioRespuesta:
    try:
        with request.app.state.database.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        logger.error("La comprobación de disponibilidad de la base de datos falló.", exc_info=error)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La base de datos no está disponible.",
        ) from error
    return EstadoServicioRespuesta(estado="ready", servicio="qrpass-api", modo="demo")


@router.get("/routes", response_model=list[RutaRespuesta], tags=["Rutas"])
def endpoint_listar_rutas(session: SessionDependency) -> list[RutaRespuesta]:
    return [RutaRespuesta.model_validate(route) for route in listar_rutas(session)]


@router.get("/fares/current", response_model=list[TarifaRespuesta], tags=["Tarifas"])
def endpoint_tarifas_vigentes(
    session: SessionDependency,
    route_id: Annotated[int | None, Query(gt=0)] = None,
    on_date: date | None = None,
) -> list[TarifaRespuesta]:
    return [TarifaRespuesta.model_validate(fare) for fare in obtener_tarifa_vigente(session, route_id, on_date)]


def _representar_usuario_autenticado(user: Usuario) -> UsuarioAutenticadoRespuesta:
    if user.nombre_usuario is None:
        raise HTTPException(status_code=409, detail="La cuenta no tiene un usuario de inicio de sesión.")
    return UsuarioAutenticadoRespuesta(
        usuario_id=user.id,
        nombre_usuario=user.nombre_usuario,
        correo=user.correo,
        nombres=user.nombres,
        roles=sorted(user_role.rol.codigo for user_role in user.roles),
    )


@auth_router.post(
    "/register",
    response_model=UsuarioAutenticadoRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una cuenta pasajera",
)
def endpoint_registrar_pasajero(payload: RegistroPasajeroSolicitud, session: SessionDependency) -> UsuarioAutenticadoRespuesta:
    email = str(payload.correo).strip().lower()
    if session.scalar(select(Usuario.id).where(Usuario.correo == email)) is not None:
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese correo.")
    passenger_role = session.scalar(select(Rol).where(Rol.codigo == "PASSENGER"))
    if passenger_role is None:
        raise HTTPException(status_code=503, detail="Los roles del sistema no están inicializados.")
    user = Usuario(
        nombres=" ".join(payload.nombres.split()),
        nombre_usuario=email,
        correo=email,
        hash_contrasena=crear_hash_contrasena(payload.contrasena),
        consentimiento_privacidad_en=datetime.datetime.now(datetime.timezone.utc),
        numero_documento=f"QRPASS-{secrets.token_hex(12)}",
        saldo_billetera=0,
        estado="active",
    )
    session.add(user)
    session.flush()
    # Una cuenta recién llegada empieza como pasajera; el registro público no
    # puede conceder por accidente permisos de conductor.
    user.roles.append(RolUsuario(rol=passenger_role))
    session.commit()
    session.refresh(user)
    return _representar_usuario_autenticado(user)


@auth_router.post("/login", response_model=InicioSesionRespuesta, summary="Iniciar sesión")
def endpoint_iniciar_sesion(payload: InicioSesionSolicitud, request: Request, session: SessionDependency) -> InicioSesionRespuesta:
    user = session.execute(
        select(Usuario)
        .options(joinedload(Usuario.roles).joinedload(RolUsuario.rol))
        .where(Usuario.nombre_usuario == payload.nombre_usuario, Usuario.estado == "active")
    ).unique().scalar_one_or_none()
    if user is None or not verificar_contrasena(payload.contrasena, user.hash_contrasena):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = crear_token_acceso(user.id, request.app.state.auth_secret)
    return InicioSesionRespuesta(
        token_acceso=token,
        vence_en_segundos=DURACION_TOKEN_SEGUNDOS,
        usuario=_representar_usuario_autenticado(user),
    )


@auth_router.get("/me", response_model=UsuarioAutenticadoRespuesta, summary="Consultar usuario y roles autenticados")
def endpoint_usuario_actual(user: UsuarioAutenticado) -> UsuarioAutenticadoRespuesta:
    return _representar_usuario_autenticado(user)


@driver_router.get(
    "/demo/assignment",
    response_model=AsignacionConductorRespuesta,
    summary="Consultar asignación de conductor de demostración",
)
def endpoint_asignacion_conductor(
    user: Annotated[Usuario, Depends(requerir_rol("DRIVER"))],
    session: SessionDependency,
) -> AsignacionConductorRespuesta:
    shift = obtener_asignacion_conductor(session, user)
    driver = session.get(Conductor, user.id)
    if shift is None or driver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La cuenta no tiene una asignación de demostración disponible.",
        )
    return AsignacionConductorRespuesta(
        nombre_conductor=user.nombres,
        numero_licencia=driver.numero_licencia,
        ruta_id=shift.ruta_id,
        nombre_ruta=shift.ruta.nombre,
        placa_vehiculo=shift.vehiculo.placa,
        estado_turno=shift.estado,
    )


def _representar_turno(summary: ResumenTurnoConductor) -> TurnoConductorRespuesta:
    shift = summary["shift"]
    return TurnoConductorRespuesta(
        turno_id=shift.id,
        ruta_id=shift.ruta_id,
        nombre_ruta=shift.ruta.nombre,
        placa_vehiculo=shift.vehiculo.placa,
        estado=shift.estado,
        inicia_en=shift.inicia_en,
        finaliza_en=shift.finaliza_en,
        total_efectivo=summary["cash"],
        total_qr=summary["qr"],
        total_tarjeta=summary["card"],
        cantidad_pagos=summary["payment_count"],
        efectivo_contado=shift.efectivo_contado,
        diferencia_efectivo=shift.diferencia_efectivo,
        movimientos=[
            MovimientoTurnoRespuesta(
                pago_id=entry["payment_id"],
                nombre_ruta=entry["route_name"],
                medio=entry["method"],
                monto=entry["amount"],
                creado_en=entry["created_at"],
            )
            for entry in summary["entries"]
        ],
    )


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


@driver_router.get("/shift", response_model=TurnoConductorRespuesta, summary="Consultar recaudo del turno activo")
def endpoint_turno_conductor(
    user: Annotated[Usuario, Depends(requerir_rol("DRIVER"))],
    session: SessionDependency,
) -> TurnoConductorRespuesta:
    summary = resumir_turno_conductor(session, user)
    if summary is None:
        raise HTTPException(status_code=404, detail="No hay un turno activo asignado.")
    return _representar_turno(summary)


@driver_router.get(
    "/shifts/history",
    response_model=list[TurnoConductorRespuesta],
    summary="Consultar los cierres de turno recientes",
)
def endpoint_historial_turnos(
    user: Annotated[Usuario, Depends(requerir_rol("DRIVER"))],
    session: SessionDependency,
) -> list[TurnoConductorRespuesta]:
    return [_representar_turno(summary) for summary in consultar_historial_turnos(session, user)]


@driver_router.post("/shift/start", response_model=TurnoConductorRespuesta, summary="Iniciar el turno asignado")
def endpoint_iniciar_turno(
    route_id: Annotated[int, Query(gt=0)],
    user: Annotated[Usuario, Depends(requerir_rol("DRIVER"))],
    session: SessionDependency,
) -> TurnoConductorRespuesta:
    shift = obtener_turno_activo_conductor(session, user)
    if shift is not None:
        if shift.ruta_id != route_id:
            raise HTTPException(status_code=403, detail="Solo puedes iniciar la ruta asignada.")
        summary = resumir_turno_conductor(session, user)
        if summary is None:
            raise HTTPException(status_code=409, detail="No se pudo consultar el turno activo.")
        return _representar_turno(summary)
    shift = obtener_asignacion_conductor(session, user)
    if shift is None:
        raise HTTPException(status_code=409, detail="No hay una asignación para iniciar.")
    if shift.ruta_id != route_id:
        raise HTTPException(status_code=403, detail="Solo puedes iniciar la ruta asignada.")
    shift.estado = "active"
    shift.inicia_en = datetime.datetime.now(datetime.timezone.utc)
    session.commit()
    summary = resumir_turno_conductor(session, user)
    if summary is None:
        raise HTTPException(status_code=409, detail="No se pudo iniciar el turno asignado.")
    return _representar_turno(summary)


@driver_router.post("/shift/payments", response_model=ReciboPago, status_code=status.HTTP_201_CREATED)
def endpoint_registrar_pago_conductor(
    payload: PagoConductorSolicitud,
    user: Annotated[Usuario, Depends(requerir_rol("DRIVER"))],
    session: SessionDependency,
) -> ReciboPago:
    payment, trip, balance = registrar_pago_conductor(
        session, user, payload.medio, payload.tipo_tarjeta.value if payload.tipo_tarjeta else None,
        payload.clave_idempotencia,
    )
    return ReciboPago(
        pago_id=payment.id, viaje_id=trip.id, ruta_id=trip.ruta_id,
        nombre_ruta=trip.ruta.nombre, medio=payment.medio, tipo_tarjeta=payload.tipo_tarjeta.value if payload.tipo_tarjeta else None,
        tipo_movimiento=payment.tipo_movimiento, monto=payment.monto, saldo_billetera=balance,
        estado=payment.estado, creado_en=payment.creado_en,
    )


@driver_router.post("/shift/close", response_model=CierreTurnoRespuesta, summary="Cerrar y consolidar un turno")
def endpoint_cerrar_turno(
    payload: CierreTurnoSolicitud,
    user: Annotated[Usuario, Depends(requerir_rol("DRIVER"))],
    session: SessionDependency,
) -> CierreTurnoRespuesta:
    summary = cerrar_turno_conductor(session, user, payload.efectivo_contado)
    return CierreTurnoRespuesta(turno=_representar_turno(summary), cerrado=True)


@driver_router.post("/qr/validate", response_model=ReciboPago, status_code=status.HTTP_201_CREATED)
def endpoint_validar_qr_pasajero(
    payload: ValidacionQrConductorSolicitud,
    request: Request,
    user: Annotated[Usuario, Depends(requerir_rol("DRIVER"))],
    session: SessionDependency,
) -> ReciboPago:
    payment, trip, balance = validar_y_canjear_qr(
        session, user, payload.token, request.app.state.auth_secret, payload.clave_idempotencia,
    )
    return ReciboPago(
        pago_id=payment.id, viaje_id=trip.id, ruta_id=trip.ruta_id,
        nombre_ruta=trip.ruta.nombre, medio=payment.medio, tipo_movimiento=payment.tipo_movimiento,
        monto=payment.monto, saldo_billetera=balance, estado=payment.estado,
        creado_en=payment.creado_en,
    )


@demo_router.get("", response_model=CuentaRespuesta, summary="Consultar la cuenta autenticada")
def endpoint_cuenta_demo(user: UsuarioAutenticado) -> CuentaRespuesta:
    return CuentaRespuesta(usuario_id=user.id, nombres=user.nombres, saldo_billetera=user.saldo_billetera)


@demo_router.post("/qr", response_model=CodigoQrRespuesta, status_code=status.HTTP_201_CREATED)
def endpoint_generar_qr_demo(
    payload: CrearCodigoQrSolicitud,
    request: Request,
    user: UsuarioAutenticado,
    session: SessionDependency,
) -> CodigoQrRespuesta:
    qr_code = crear_codigo_qr(
        session, user, payload.ruta_id, payload.vigencia_minutos, request.app.state.auth_secret,
    )
    return CodigoQrRespuesta(
        codigo_qr_id=qr_code.id,
        token=qr_code.token,
        estado=qr_code.estado,
        creado_en=qr_code.creado_en,
        vence_en=qr_code.vence_en,
        imagen_data_uri=crear_imagen_qr(qr_code.token),
    )


@router.get("/payments/history", response_model=list[HistorialPagosRespuesta], tags=["Pagos"], summary="Consultar el historial unificado de pagos")
def endpoint_historial_pagos(user: UsuarioAutenticado, session: SessionDependency) -> list[HistorialPagosRespuesta]:
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


@router.get("/trips", response_model=list[ViajeRespuesta], tags=["Viajes"], summary="Consultar el historial de viajes")
def endpoint_historial_viajes(user: UsuarioAutenticado, session: SessionDependency) -> list[ViajeRespuesta]:
    return [_representar_viaje(trip) for trip in listar_viajes(session, user)]


@router.get("/trips/{trip_id}", response_model=ViajeRespuesta, tags=["Viajes"], summary="Consultar el detalle de un viaje")
def endpoint_detalle_viaje(trip_id: int, user: UsuarioAutenticado, session: SessionDependency) -> ViajeRespuesta:
    return _representar_viaje(obtener_viaje(session, user, trip_id))


@demo_router.get("/trips", response_model=list[ViajeRespuesta], summary="Consultar el historial de prueba")
def endpoint_historial_viajes_demo(user: UsuarioAutenticado, session: SessionDependency) -> list[ViajeRespuesta]:
    return [_representar_viaje(trip) for trip in listar_viajes(session, user)]


@demo_router.post("/payments", response_model=ReciboPago, status_code=status.HTTP_201_CREATED)
def endpoint_pagar_viaje(payload: CrearPagoSolicitud, user: UsuarioAutenticado, session: SessionDependency) -> ReciboPago:
    payment, trip, wallet_balance = crear_pago(session, user, payload)
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


@demo_router.post("/top-ups", response_model=ReciboRecarga, status_code=status.HTTP_201_CREATED)
def endpoint_recargar_billetera(payload: CrearRecargaSolicitud, user: UsuarioAutenticado, session: SessionDependency) -> ReciboRecarga:
    payment = crear_recarga(session, user, payload)
    return ReciboRecarga(
        pago_id=payment.id,
        monto=payment.monto,
        saldo_billetera=payment.saldo_posterior,
        estado=payment.estado,
        creado_en=payment.creado_en,
    )


@demo_router.post("/transfers", response_model=TransbordoRespuesta, status_code=status.HTTP_201_CREATED)
def endpoint_transferir_viaje(payload: CrearTransbordoSolicitud, user: UsuarioAutenticado, session: SessionDependency) -> TransbordoRespuesta:
    transfer = crear_transbordo(session, user, payload)
    return TransbordoRespuesta(
        transbordo_id=transfer.id,
        viaje_origen_id=transfer.viaje_origen_id,
        ruta_origen=transfer.viaje_origen.ruta.nombre,
        ruta_destino_id=transfer.ruta_destino_id,
        ruta_destino=transfer.ruta_destino.nombre,
        creado_en=transfer.creado_en,
    )


router.include_router(auth_router)
router.include_router(driver_router)
router.include_router(demo_router)
