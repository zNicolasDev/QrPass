# Backend QrPass

API de QrPass construida con **FastAPI**, **SQLAlchemy 2** y **Pydantic**. Los modelos de persistencia están en `app/models/` y los DTOs de entrada/salida HTTP en `app/dtos/`.

## Iniciar en desarrollo

Desde esta carpeta:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m app.management init
python -m app.management import-catalog
python -m uvicorn app.core.main:app --reload
```

`init` crea el esquema de `qrpass.db` (SQLite local) y los roles del sistema. `import-catalog` carga rutas y tarifas desde `app/datos_maestros/rutas_tarifas.json` de forma idempotente. No se crean cuentas automáticamente. Documentación interactiva: `http://127.0.0.1:8000/docs`.

Copia `.env.example` como referencia para configurar `QR_PASS_DATABASE_URL`, `QR_PASS_CORS_ORIGINS` y `QR_PASS_AUTH_SECRET` en el proceso. La aplicación no carga automáticamente un archivo `.env`.

## Cuentas y aprovisionamiento

Los pasajeros se registran desde `POST /auth/register` o desde la interfaz. Las cuentas de conductor y administración se crean con la gestión de QrPass:

```powershell
python -m app.management create-driver --nombre "Conductor QrPass" --correo conductor@qrpass.com --contrasena "Clave-Segura-2026" --licencia LIC-001 --ruta 24 --placa ABC123
python -m app.management create-admin --nombre "Administrador QrPass" --correo admin@qrpass.com --contrasena "Clave-Segura-2026"
python -m app.management status
```

`create-driver` asigna los roles `PASSENGER` y `DRIVER`; si se indica `--ruta` y `--placa`, también registra el turno asignado. `create-admin` asigna los roles `PASSENGER` y `ADMIN` para que la cuenta pueda usar la interfaz y consultar las métricas globales. Las contraseñas se solicitan de forma interactiva si se omite `--contrasena` y deben tener al menos 12 caracteres. La API valida los roles y protege las operaciones de conductor y administración. Los tokens vencen en una hora. En desarrollo, si falta `QR_PASS_AUTH_SECRET`, se genera un secreto aleatorio y las sesiones dejan de servir al reiniciar. Producción requiere `QR_PASS_ENV=production` y un secreto de al menos 32 bytes.

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
| GET | `/account` | Billetera de la cuenta autenticada |
| GET | `/payments/history` | Historial autenticado unificado de ingresos y egresos |
| GET | `/trips` | Historial de viajes del usuario autenticado |
| GET | `/trips/{trip_id}` | Detalle de un viaje propio |
| POST | `/account/qr/validate` | El pasajero escanea el QR firmado que muestra el bus y paga con su saldo |
| POST | `/account/payments` | Pago en efectivo o tarjeta; el saldo requiere escanear QR del bus |
| POST | `/account/top-ups` | Recarga idempotente de la billetera QrPass |
| POST | `/account/transfers` | Traspaso único a otra ruta dentro de 20 minutos |
| GET | `/admin/metrics` | Métricas globales de recaudo; requiere rol `ADMIN` |
| GET | `/driver/assignment` | Asignación operativa; requiere rol `DRIVER` |
| GET | `/driver/shift` | Totales del turno activo; requiere rol `DRIVER` |
| GET | `/driver/shifts/history` | Últimos 20 cierres del conductor |
| POST | `/driver/shift/start?route_id={id}` | Inicio de turno asignado |
| POST | `/driver/shift/payments` | Registro de efectivo o tarjeta en el turno |
| POST | `/driver/shift/qr` | Genera el QR temporal del turno activo para mostrarlo en el bus |
| POST | `/driver/shift/close` | Cierre de turno y conciliación |

## Carpetas y archivos

- `app/seguridad/auth.py`: autenticación y permisos por rol.
- `app/controllers/`: controladores HTTP organizados por sistema, autenticación, pasajero, conductor y administración.
- `app/dtos/`: DTOs; clases y campos internos en español, con alias que conservan las claves actuales de JSON para solicitudes y respuestas.
- `app/servicios/`: reglas de pagos, tarifas, QR, traspasos, turnos, usuarios y catálogo.
- `app/models/`: modelos; clases, atributos y relaciones SQLAlchemy en español. Los nombres físicos de tablas y columnas siguen iguales mediante los nombres explícitos de SQLAlchemy.
- `app/core/database.py`: conexión, sesiones, roles del sistema y compatibilidad SQLite.
- `app/seguridad/passwords.py`: hash y verificación de contraseñas.
- `app/core/main.py`: creación de la aplicación FastAPI.
- `app/management.py`: comandos de inicialización, catálogo y aprovisionamiento de cuentas.
- `app/datos_maestros/rutas_tarifas.json`: catálogo maestro de rutas y tarifas.
- `tests/test_api.py`: pruebas con base de datos aislada.
- `../documentacion/arquitectura.md`: diagramas y flujos.
- `../documentacion/trazabilidad.md`: estado de requisitos y pendientes.

Ejecuta las pruebas desde esta carpeta:

```powershell
python -m pytest
```

## Límites antes de producción

Esta API usa exclusivamente la billetera interna QrPass: no mueve dinero real ni procesa pagos con tarjeta mediante una pasarela o POS. Los QR se verifican en línea mediante HMAC; no se debe distribuir esa clave a validadores sin conexión. Una modalidad offline requiere firma asimétrica, gestión de claves y controles contra el doble gasto.

`/health` es una señal de vida de la API; `/ready` prueba conectividad con la base de datos y responde 503 si no puede consultarla. En pagos, el débito/recarga y sus filas de pago/viaje se escriben dentro de la transacción SQLAlchemy de la solicitud. Las pruebas `test_failed_payment_commit_rolls_back_balance_payment_and_trip` y `test_failed_qr_redemption_commit_restores_qr_balance_payment_and_trip` inyectan un fallo antes del commit y confirman que no quedan débito, el QR sigue disponible para reintentar y no quedan registros parciales.

SQLite y la inicialización de desarrollo no sustituyen migraciones versionadas ni una base de producción compartida. La compatibilidad actual hace ajustes de esquema SQLite durante la inicialización, por lo que el proceso de migraciones debe formalizarse antes de evolucionar datos persistidos. TLS 1.3 depende del proxy o alojamiento. También hacen falta pruebas de concurrencia/carga, monitoreo y validación jurídica y operativa. No proceses pagos con dinero real ni almacenes datos financieros sensibles.
