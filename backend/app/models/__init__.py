# Este paquete importa y reexporta las entidades para registrar sus tablas.
"""Entidades SQLAlchemy que representan los datos persistidos de QrPass."""

# Reexporta modelos desde app.models y los importa para registrar sus tablas
# antes de que Base.metadata.create_all construya el esquema.
from app.models.base import Base
from app.models.dispositivo_abordo import DispositivoAbordo
from app.models.tarjeta import Tarjeta
from app.models.conductor import Conductor
from app.models.tarifa import Tarifa
from app.models.sincronizacion_offline import SincronizacionOffline
from app.models.pago import Pago
from app.models.codigo_qr import CodigoQr
from app.models.rol import Rol
from app.models.ruta import Ruta
from app.models.turno import Turno
from app.models.empresa_transporte import EmpresaTransporte
from app.models.transbordo import Transbordo
from app.models.viaje import Viaje
from app.models.usuario import Usuario
from app.models.rol_usuario import RolUsuario
from app.models.vehiculo import Vehiculo

__all__ = [
    "Base",
    'DispositivoAbordo',
    'Tarjeta',
    'Conductor',
    'Tarifa',
    'SincronizacionOffline',
    'Pago',
    'CodigoQr',
    'Rol',
    'Ruta',
    'Turno',
    'EmpresaTransporte',
    'Transbordo',
    'Viaje',
    'Usuario',
    'RolUsuario',
    'Vehiculo',
]
