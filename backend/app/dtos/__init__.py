"""DTOs Pydantic para validar solicitudes y definir respuestas de la API."""

from app.dtos.cuenta import CuentaRespuesta
from app.dtos.autenticacion import UsuarioAutenticadoRespuesta, InicioSesionSolicitud, InicioSesionRespuesta, RegistroPasajeroSolicitud
from app.dtos.conductor import (
    AsignacionConductorRespuesta,
    PagoConductorSolicitud,
    ValidacionQrConductorSolicitud,
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
from app.dtos.codigo_qr import CrearCodigoQrSolicitud, CodigoQrRespuesta
from app.dtos.ruta import TarifaRespuesta, RutaRespuesta
from app.dtos.sistema import EstadoServicioRespuesta
from app.dtos.transbordo import CrearTransbordoSolicitud, TransbordoRespuesta
from app.dtos.viaje import ViajeRespuesta

__all__ = [
    'CuentaRespuesta',
    'UsuarioAutenticadoRespuesta',
    'TipoTarjeta',
    'AsignacionConductorRespuesta',
    'PagoConductorSolicitud',
    'ValidacionQrConductorSolicitud',
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
    'CrearCodigoQrSolicitud',
    'CodigoQrRespuesta',
    'RutaRespuesta',
    'CierreTurnoRespuesta',
    'CrearRecargaSolicitud',
    'ReciboRecarga',
    'CrearTransbordoSolicitud',
    'TransbordoRespuesta',
    'ViajeRespuesta',
]
