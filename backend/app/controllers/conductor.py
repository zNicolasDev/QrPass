from __future__ import annotations
# Este controlador recibe las operaciónes del conductor y delega las reglas al servicio.
from typing import Annotated
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import Request
from fastapi import status
from sqlalchemy.orm import Session
from app.auth import requerir_rol
from app.database import obtener_sesion
from app.dtos import AsignacionConductorRespuesta
from app.dtos import MovimientoTurnoRespuesta
from app.dtos import CierreTurnoSolicitud
from app.dtos import PagoConductorSolicitud
from app.dtos import CodigoQrRespuesta
from app.dtos import TurnoConductorRespuesta
from app.dtos import ReciboPago
from app.dtos import CierreTurnoRespuesta
from app.models import Usuario
from app.services import cerrar_turno_conductor
from app.services import consultar_historial_turnos
from app.services import resumir_turno_conductor
from app.services import ResumenTurnoConductor
from app.services import registrar_pago_conductor
from app.services import crear_qr_turno_conductor
from app.services import crear_imagen_qr
from app.services import obtener_datos_asignacion_conductor
from app.services import iniciar_turno_conductor




SessionDependency = Annotated[Session, Depends(obtener_sesion)]
driver_router = APIRouter(prefix="/driver", tags=["Conductor"])

# Devuelve la ruta y el vehículo asignados al conductor.
@driver_router.get(
    "/demo/assignment",
    response_model=AsignacionConductorRespuesta,
    summary="Consultar asignación de conductor de demostración",
)
def endpoint_asignacion_conductor(
    user: Annotated[Usuario, Depends(requerir_rol("DRIVER"))],
    session: SessionDependency,
) -> AsignacionConductorRespuesta:
    # El permiso DRIVER se comprueba en la dependencia antes de ejecutar esta función.
    # El servicio consulta la asignación; aquí solo se revisa si hay datos que mostrar.
    driver, shift = obtener_datos_asignacion_conductor(session, user)
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


# Convierte el resumen del servicio al formato que espera la consola del conductor.
def _representar_turno(summary: ResumenTurnoConductor) -> TurnoConductorRespuesta:
    shift = summary["shift"]
    # Cada movimiento ya viene resumido por el servicio; aquí solo se renombran
    # sus datos para que coincidan con los campos del DTO de respuesta.
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

# Devuelve los totales del turno que esta activo.
@driver_router.get("/shift", response_model=TurnoConductorRespuesta, summary="Consultar recaudo del turno activo")
def endpoint_turno_conductor(
    user: Annotated[Usuario, Depends(requerir_rol("DRIVER"))],
    session: SessionDependency,
) -> TurnoConductorRespuesta:
    # El servicio busca el turno activo y calcula totales por medio de pago.
    summary = resumir_turno_conductor(session, user)
    if summary is None:
        raise HTTPException(status_code=404, detail="No hay un turno activo asignado.")
    return _representar_turno(summary)


# Presenta el QR que el bus muestra para que los pasajeros lo escaneen.
@driver_router.post("/shift/qr", response_model=CodigoQrRespuesta, status_code=status.HTTP_201_CREATED, summary="Generar el QR de abordaje del bus")
def endpoint_qr_turno_conductor(
    user: Annotated[Usuario, Depends(requerir_rol("DRIVER"))],
    session: SessionDependency,
    request: Request,
    renovar: Annotated[bool, Query(alias="renew")] = False,
) -> CodigoQrRespuesta:
    qr_code = crear_qr_turno_conductor(session, user, request.app.state.auth_secret, renovar)
    return CodigoQrRespuesta(
        codigo_qr_id=qr_code.id,
        token=qr_code.token,
        estado=qr_code.estado,
        creado_en=qr_code.creado_en,
        vence_en=qr_code.vence_en,
        imagen_data_uri=crear_imagen_qr(qr_code.token),
    )

# Devuelve los últimos cierres del conductor.
@driver_router.get(
    "/shifts/history",
    response_model=list[TurnoConductorRespuesta],
    summary="Consultar los cierres de turno recientes",
)
def endpoint_historial_turnos(
    user: Annotated[Usuario, Depends(requerir_rol("DRIVER"))],
    session: SessionDependency,
) -> list[TurnoConductorRespuesta]:
    # El servicio entrega los últimos turnos cerrados de este conductor.
    return [_representar_turno(summary) for summary in consultar_historial_turnos(session, user)]

# Comprueba la asignación y marca el turno como iniciado.
@driver_router.post("/shift/start", response_model=TurnoConductorRespuesta, summary="Iniciar el turno asignado")
def endpoint_iniciar_turno(
    route_id: Annotated[int, Query(gt=0)],
    user: Annotated[Usuario, Depends(requerir_rol("DRIVER"))],
    session: SessionDependency,
) -> TurnoConductorRespuesta:
    # La ruta llega como parámetro de URL. El servicio verifica que sea la
    # asignada y guarda el inicio antes de devolver el resumen actualizado.
    summary = iniciar_turno_conductor(session, user, route_id)
    return _representar_turno(summary)

# Registra un recaudo manual en el turno activo.
@driver_router.post("/shift/payments", response_model=ReciboPago, status_code=status.HTTP_201_CREATED)
def endpoint_registrar_pago_conductor(
    payload: PagoConductorSolicitud,
    user: Annotated[Usuario, Depends(requerir_rol("DRIVER"))],
    session: SessionDependency,
) -> ReciboPago:
    # El servicio registra el pago y el viaje dentro del turno activo.
    payment, trip, balance = registrar_pago_conductor(
        session, user, payload.medio, payload.tipo_tarjeta.value if payload.tipo_tarjeta else None,
        payload.clave_idempotencia,
    )
    # El recibo contiene el resultado confirmado, no datos inventados por pantalla.
    return ReciboPago(
        pago_id=payment.id, viaje_id=trip.id, ruta_id=trip.ruta_id,
        nombre_ruta=trip.ruta.nombre, medio=payment.medio, tipo_tarjeta=payload.tipo_tarjeta.value if payload.tipo_tarjeta else None,
        tipo_movimiento=payment.tipo_movimiento, monto=payment.monto, saldo_billetera=balance,
        estado=payment.estado, creado_en=payment.creado_en,
    )

# Cierra el turno y compara el efectivo contado con el registrado.
@driver_router.post("/shift/close", response_model=CierreTurnoRespuesta, summary="Cerrar y consolidar un turno")
def endpoint_cerrar_turno(
    payload: CierreTurnoSolicitud,
    user: Annotated[Usuario, Depends(requerir_rol("DRIVER"))],
    session: SessionDependency,
) -> CierreTurnoRespuesta:
    # El servicio marca el turno como cerrado y calcula la diferencia de efectivo.
    summary = cerrar_turno_conductor(session, user, payload.efectivo_contado)
    return CierreTurnoRespuesta(turno=_representar_turno(summary), cerrado=True)
