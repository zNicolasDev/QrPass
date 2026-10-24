# Este paquete reexporta los esquemas de solicitud y respuesta por tema.
"""DTOs Pydantic para validar solicitudes y definir respuestas de la API."""

# Reexporta los DTOs por tema para que las rutas los importen desde app.dtos.
from app.dtos.cuenta import CuentaRespuesta
from app.dtos.autenticacion import UsuarioAutenticadoRespuesta, InicioSesionSolicitud, InicioSesionRespuesta, RegistroPasajeroSolicitud
from app.dtos.conductor import (
    AsignacionConductorRespuesta,
    PagoConductorSolicitud,
    CierreTurnoSolicitud,
    MovimientoTurnoRespuesta,
    TurnoConductorRespuesta,
    CierreTurnoRespuesta,
)
from app.dtos.enumeraciones import TipoTarjeta, MedioPago
from app.dtos.pago import (
    CrearPagoSolicitud,
    HistorialPagosRespuesta,
    ReciboPago,
    CrearRecargaSolicitud,
    ReciboRecarga,
)
from app.dtos.codigo_qr import CodigoQrRespuesta, ValidacionQrPasajeroSolicitud
from app.dtos.ruta import TarifaRespuesta, RutaRespuesta
from app.dtos.sistema import EstadoServicioRespuesta
from app.dtos.transbordo import CrearTransbordoSolicitud, TransbordoRespuesta
from app.dtos.viaje import ViajeRespuesta
from app.dtos.administracion import MetricasGerencialesRespuesta, ReinicioDemoRespuesta

__all__ = [
    'CuentaRespuesta',
    'UsuarioAutenticadoRespuesta',
    'TipoTarjeta',
    'AsignacionConductorRespuesta',
    'PagoConductorSolicitud',
    'CierreTurnoSolicitud',
    'MovimientoTurnoRespuesta',
    'TurnoConductorRespuesta',
    'TarifaRespuesta',
    'EstadoServicioRespuesta',
    'InicioSesionSolicitud',
    'InicioSesionRespuesta',
    'CrearPagoSolicitud',
    'HistorialPagosRespuesta',
    'MedioPago',
    'ReciboPago',
    'RegistroPasajeroSolicitud',
    'ValidacionQrPasajeroSolicitud',
    'CodigoQrRespuesta',
    'RutaRespuesta',
    'CierreTurnoRespuesta',
    'CrearRecargaSolicitud',
    'ReciboRecarga',
    'CrearTransbordoSolicitud',
    'TransbordoRespuesta',
    'ViajeRespuesta',
    'MetricasGerencialesRespuesta',
    'ReinicioDemoRespuesta',
]
