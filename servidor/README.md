# Servidor QrPass

API de demostración construida con **FastAPI**, **SQLAlchemy 2** y **Pydantic**. Los bocetos de `../datos/entidades/` son referencia académica; los modelos que utiliza la API están en `aplicacion/modelos.py`.

## Iniciar en desarrollo

Desde esta carpeta:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn aplicacion.inicio:app --reload
```

La API crea `qrpass.db` (SQLite local), carga rutas y tarifas de ejemplo y prepara las cuentas de demostración. Documentación interactiva: `http://127.0.0.1:8000/docs`.

Copia `.env.example` como referencia para configurar `QR_PASS_DATABASE_URL`, `QR_PASS_CORS_ORIGINS` y `QR_PASS_AUTH_SECRET` en el proceso. La aplicación no carga automáticamente un archivo `.env`.

## Cuentas de demostración

| Usuario | Contraseña local predeterminada | Roles |
|---|---|---|
| `pasajero.demo` | `QrPass-Pasajero-Demo-2026` | `PASSENGER` |
| `conductor.demo` | `QrPass-Conductor-Demo-2026` | `PASSENGER`, `DRIVER` |

Son credenciales públicas de uso local; no las uses en producción. Las cuentas nuevas se registran como pasajero. La API valida los roles y protege las operaciones de conductor. Los tokens vencen en una hora. En desarrollo, si falta `QR_PASS_AUTH_SECRET`, se genera un secreto aleatorio y las sesiones dejan de servir al reiniciar. Producción requiere `QR_PASS_ENV=production`, un secreto de al menos 32 bytes y contraseñas explícitas para cuentas de demostración habilitadas.

## Rutas principales

Todos los endpoints usan el prefijo `/api/v1`.

| Método | Endpoint | Función |
|---|---|---|
| GET | `/health` | Estado del servicio |
| GET | `/routes` | Catálogo de rutas |
| GET | `/fares/current` | Tarifa vigente |
| POST | `/auth/register` | Registro de pasajero y consentimiento |
| POST | `/auth/login` | Inicio de sesión |
| GET | `/auth/me` | Identidad y roles de la sesión |
| GET | `/demo/account` | Billetera de la cuenta autenticada |
| GET | `/demo/account/trips` | Historial de viajes |
| POST | `/demo/account/qr` | QR firmado con vigencia máxima de 15 minutos |
| POST | `/demo/account/payments` | Pago de demostración por saldo, efectivo o tarjeta |
| POST | `/demo/account/top-ups` | Recarga ficticia e idempotente |
| POST | `/demo/account/transfers` | Traspaso único a otra ruta dentro de 20 minutos |
| GET | `/driver/demo/assignment` | Asignación de ejemplo; requiere rol `DRIVER` |
| GET | `/driver/shift` | Totales del turno activo; requiere rol `DRIVER` |
| GET | `/driver/shifts/history` | Últimos 20 cierres del conductor |
| POST | `/driver/shift/start?route_id={id}` | Inicio de turno asignado |
| POST | `/driver/shift/payments` | Registro de efectivo o tarjeta simulados |
| POST | `/driver/qr/validate` | Validación en línea de QR durante el turno |
| POST | `/driver/shift/close` | Cierre de turno y conciliación |

## Carpetas y archivos

- `aplicacion/sesion.py`: autenticación y permisos por rol.
- `aplicacion/rutas.py`: endpoints HTTP.
- `aplicacion/esquemas.py`: validación de solicitudes y respuestas.
- `aplicacion/servicios.py`: reglas de pagos, tarifas, QR, traspasos y turnos.
- `aplicacion/modelos.py`: tablas e invariantes de SQLAlchemy.
- `aplicacion/base_datos.py`: conexión, sesiones, datos iniciales y compatibilidad SQLite.
- `aplicacion/contrasenas.py`: hash y verificación de contraseñas.
- `aplicacion/inicio.py`: creación de la aplicación FastAPI.
- `pruebas/test_api.py`: pruebas con base de datos aislada.
- `documentacion/arquitectura.md`: diagramas y flujos.
- `documentacion/trazabilidad.md`: estado de requisitos y pendientes.

Ejecuta las pruebas desde esta carpeta:

```powershell
python -m pytest
```

## Límites antes de producción

Esta API no mueve dinero real: los pagos con tarjeta y las recargas son ficticios, y no hay integración POS o bancaria. Los QR se verifican en línea mediante HMAC; no se debe distribuir esa clave a validadores sin conexión. Una modalidad offline requiere firma asimétrica, gestión de claves y controles contra el doble gasto.

SQLite y la inicialización de desarrollo no sustituyen migraciones versionadas ni una base de producción compartida. TLS 1.3 depende del proxy o alojamiento. También hacen falta pruebas de carga, monitoreo y validación jurídica y operativa. No almacenes datos personales o financieros reales en este prototipo.
