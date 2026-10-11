# Backend QrPass

API de demostración construida con **FastAPI**, **SQLAlchemy 2** y **Pydantic**. Los modelos de persistencia están en `app/models/` y los DTOs de entrada/salida HTTP en `app/dtos/`.

## Iniciar en desarrollo

Desde esta carpeta:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

La API crea `qrpass.db` (SQLite local), carga rutas y tarifas de ejemplo y prepara las cuentas de demostración. Documentación interactiva: `http://127.0.0.1:8000/docs`.

Copia `.env.example` como referencia para configurar `QR_PASS_DATABASE_URL`, `QR_PASS_CORS_ORIGINS` y `QR_PASS_AUTH_SECRET` en el proceso. La aplicación no carga automáticamente un archivo `.env`.

## Cuentas de demostración

| Usuario | Contraseña local predeterminada | Roles |
|---|---|---|
| `pasajero.demo` | `QrPass-Pasajero-Demo-2026` | `PASSENGER` |
| `conductor.demo` | `QrPass-Conductor-Demo-2026` | `PASSENGER`, `DRIVER` |

Son credenciales públicas de uso local; no las uses en producción. Las cuentas nuevas se registran como pasajero. La API valida los roles y protege las operaciones de conductor. Los tokens vencen en una hora. En desarrollo, si falta `QR_PASS_AUTH_SECRET`, se genera un secreto aleatorio y las sesiones dejan de servir al reiniciar. Producción requiere `QR_PASS_ENV=production`, un secreto de al menos 32 bytes y contraseñas explícitas para cuentas de demostración habilitadas.

## Modelos y DTOs

- `app/models/`: modelos SQLAlchemy que representan tablas, columnas, relaciones y restricciones de persistencia. Cada entidad tiene un archivo propio con nombre en español, por ejemplo `usuario.py`, `pago.py`, `ruta.py` y `viaje.py`; `base.py` contiene la base declarativa que comparten.
- `app/dtos/`: modelos Pydantic que validan solicitudes y definen las respuestas HTTP, organizados por tema en archivos con nombres en español (`autenticacion.py`, `pago.py`, `conductor.py`, etc.). `__init__.py` reexporta los tipos para facilitar los imports.
- Un DTO no sustituye ni replica la entidad ORM: el modelo describe el almacenamiento y las relaciones; el DTO marca el contrato de entrada/salida.
- `tests/test_models_dtos.py`: verifica el registro de tablas, relaciones ORM, persistencia y validaciones/serialización de DTOs.
- `tests/test_api.py`: verifica flujos integrados existentes mediante FastAPI y una base SQLite de prueba.

Desde esta carpeta, ejecuta `python -m pytest -q`. Para correr solamente las pruebas de modelos y DTOs: `python -m pytest -q tests/test_models_dtos.py`.

## Rutas principales

Todos los endpoints usan el prefijo `/api/v1`.

| Método | Endpoint | Función |
|---|---|---|
| GET | `/health` | Estado del servicio |
| GET | `/ready` | Disponibilidad del servicio con verificación `SELECT 1` sobre la base |
| GET | `/routes` | Catálogo de rutas |
| GET | `/fares/current` | Tarifa vigente |
| POST | `/auth/register` | Registro de pasajero y consentimiento |
| POST | `/auth/login` | Inicio de sesión |
| GET | `/auth/me` | Identidad y roles de la sesión |
| GET | `/demo/account` | Billetera de la cuenta autenticada |
| GET | `/demo/account/trips` | Historial de viajes |
| GET | `/payments/history` | Historial autenticado unificado de ingresos y egresos |
| GET | `/trips` | Historial de viajes del usuario autenticado |
| GET | `/trips/{trip_id}` | Detalle de un viaje propio |
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

- `app/auth.py`: autenticación y permisos por rol.
- `app/routes.py`: endpoints HTTP.
- `app/dtos/`: DTOs; clases y campos internos en español, con alias que conservan las claves actuales de JSON para solicitudes y respuestas.
- `app/services.py`: reglas de pagos, tarifas, QR, traspasos y turnos.
- `app/models/`: modelos; clases, atributos y relaciones SQLAlchemy en español. Los nombres físicos de tablas y columnas siguen iguales mediante los nombres explícitos de SQLAlchemy.
- `app/database.py`: conexión, sesiones, datos iniciales y compatibilidad SQLite.
- `app/passwords.py`: hash y verificación de contraseñas.
- `app/main.py`: creación de la aplicación FastAPI.
- `tests/test_api.py`: pruebas con base de datos aislada.
- `docs/arquitectura.md`: diagramas y flujos.
- `docs/trazabilidad.md`: estado de requisitos y pendientes.

Ejecuta las pruebas desde esta carpeta:

```powershell
python -m pytest
```

## Límites antes de producción

Esta API no mueve dinero real: los pagos con tarjeta y las recargas son ficticios, y no hay integración POS o bancaria. Los QR se verifican en línea mediante HMAC; no se debe distribuir esa clave a validadores sin conexión. Una modalidad offline requiere firma asimétrica, gestión de claves y controles contra el doble gasto.

`/health` es una señal de vida de la API; `/ready` prueba conectividad con la base de datos y responde 503 si no puede consultarla. En pagos, el débito/recarga y sus filas de pago/viaje se escriben dentro de la transacción SQLAlchemy de la solicitud. Las pruebas `test_failed_payment_commit_rolls_back_balance_payment_and_trip` y `test_failed_qr_redemption_commit_restores_qr_balance_payment_and_trip` inyectan un fallo antes del commit y confirman que no quedan débito, consumo de QR ni registros parciales.

SQLite y la inicialización de desarrollo no sustituyen migraciones versionadas ni una base de producción compartida. La compatibilidad actual hace ajustes de esquema SQLite durante la inicialización, por lo que el proceso de migraciones debe formalizarse antes de evolucionar datos persistidos. TLS 1.3 depende del proxy o alojamiento. También hacen falta pruebas de concurrencia/carga, monitoreo y validación jurídica y operativa. No almacenes datos personales o financieros reales en este prototipo.
