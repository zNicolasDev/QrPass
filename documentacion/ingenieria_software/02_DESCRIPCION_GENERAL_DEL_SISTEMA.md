# 2. DESCRIPCIÓN GENERAL DEL SISTEMA

## 2.1. Propósito
Proveer una plataforma de demostración para el cobro de pasajes con distintos medios: efectivo, tarjeta y saldo mediante escaneo de QR del bus. Todo con control por roles, idempotencia, validación de turnos y trazabilidad financiera.

## 2.2. Alcance
- Autenticación y registro de pasajero
- Gestión de billetera (recargas)
- Cobro de pasaje (efectivo, tarjeta y QR del bus con saldo)
- Gestión de turno del conductor (iniciar, generar QR, cerrar)
- Historial de pagos y viajes
- Transbordos (ventana de 20 minutos)
- Consulta de rutas, tarifas vigentes y estado del servicio

## 2.3. Actores
| Actor | Descripción |
|---|---|
| Pasajero | Usuario con rol PASSENGER. Puede recargar, pagar, consultar historial y aplicar transbordos. |
| Conductor | Usuario con rol DRIVER (puede tener también PASSENGER). Gestiona su turno y genera QR. |
| Sistema (API) | Encargado de validar reglas, firmas, idempotencia e integridad de datos. |
| Administrador/Demo | Consultas de métricas y utilidades de demostración. |

## 2.4. Restricciones
- Entorno demo: no se procesan pagos reales
- SQLite para entorno de demostración (`qrpass.db` o `:memory:` para pruebas)
- Autenticación por token Bearer firmado con `QR_PASS_AUTH_SECRET`
- Claves foráneas activas en SQLite
- Validación con Pydantic v2
