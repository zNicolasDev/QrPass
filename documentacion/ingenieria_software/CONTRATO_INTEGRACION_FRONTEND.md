# Contrato de integración del frontend

Cada fila relaciona requisitos funcionales (RF), pantalla, solicitud HTTP y respuesta que consume la interfaz. Los módulos agrupan varios RF; sus subrequisitos conservan los identificadores del documento de requisitos.

Todos los endpoints de la tabla usan el prefijo `/api/v1` y las operaciones autenticadas envían `Authorization: Bearer <access_token>`. Los cuerpos y respuestas muestran las claves JSON públicas, no los nombres internos de los modelos.

## Módulo 1: Autenticación y cuenta

| RF | Pantalla | Método y endpoint | JSON de entrada | Respuesta principal |
|---|---|---|---|---|
| RF-01 | `frontend/login.html` | `POST /auth/login` | `{"username":"<usuario o correo>","password":"<contraseña>"}` | `access_token`, `token_type`, `expires_in` y `user` con `user_id`, `username`, `email`, `names`, `roles`, `mode`. |
| RF-02 | `frontend/login.html` — crear cuenta | `POST /auth/register` | `{"names":"<nombre>","email":"<correo>","password":"<contraseña>","privacy_consent":true}` | `user_id`, `username`, `email`, `names`, `roles`, `mode`. Después, la interfaz inicia sesión con la cuenta creada. |
| RF-03 | `frontend/index.html` — selección del espacio | `GET /auth/me` | No aplica; requiere token Bearer. | Perfil autenticado: `user_id`, `username`, `email`, `names`, `roles`, `mode`. El servidor determina y valida los roles. |

## Módulo 2: Pasajero, pagos y viajes

| RF | Pantalla | Método y endpoint | JSON de entrada | Respuesta principal |
|---|---|---|---|---|
| RF-04, RF-12 | `frontend/pasajero.html` — Recargar saldo | `POST /demo/account/top-ups` | `{"amount":<valor>,"idempotency_key":"<clave>"}` | Recibo: `payment_id`, `movement_type`, `amount`, `currency`, `wallet_balance`, `status`, `created_at`, `mode`. La clave de idempotencia protege los reintentos. |
| RF-05, RF-09, RF-12 | `frontend/pasajero.html` — Pagar pasaje | `POST /demo/account/payments` | `{"route_id":<id>,"method":"cash|card","card_type":"debit|credit","destination":"<opcional>","idempotency_key":"<clave>"}`. `card_type` y `destination` se incluyen solo cuando aplican. | Recibo de pago y viaje: `payment_id`, `trip_id`, `route_id`, `route_name`, `method`, `amount`, `wallet_balance`, `status`, `created_at`, entre otros. |
| RF-06, RF-08, RF-12 | `frontend/pasajero.html` — Escanear QR | `POST /demo/account/qr/validate` | `{"token":"<contenido del QR del bus>","idempotency_key":"<clave>"}` | Recibo del viaje: `payment_id`, `trip_id`, `route_id`, `route_name`, `method`, `amount`, `wallet_balance`, `status`, `created_at`. |
| RF-10 | `frontend/pasajero.html` — Historial | `GET /payments/history`, `GET /demo/account/trips` | No aplica; requiere token Bearer. | Listas de movimientos y viajes propios, incluyendo importes, fechas, rutas y, para pagos, saldo anterior y posterior. |
| RF-11 | `frontend/pasajero.html` — Traspaso de ruta | `POST /demo/account/transfers` | `{"trip_id":<viaje>,"destination_route_id":<ruta destino>}` | `transfer_id`, `origin_trip_id`, `origin_route`, `destination_route_id`, `destination_route`, `additional_charge`, `created_at`, `mode`. |

## Módulo 3: Operación del conductor

| RF | Pantalla | Método y endpoint | JSON de entrada | Respuesta principal |
|---|---|---|---|---|
| RF-07 | `frontend/conductor.html` — Mi turno | `POST /driver/shift/start?route_id=<id>` | No aplica en el cuerpo; la ruta va en la URL. | Resumen del turno: `shift_id`, `route_id`, `route_name`, `vehicle_plate`, `status`, fechas, totales y movimientos. |
| RF-07, RF-08 | `frontend/conductor.html` — QR del bus | `POST /driver/shift/qr` | No aplica; para renovar se usa `?renew=true`. | `qr_id`, `token`, `status`, `created_at`, `expires_at`, `scannable`, `image_data_uri`, `mode`. El pasajero escanea este QR desde su flujo. |
| RF-07 | `frontend/conductor.html` — Registrar recaudo | `POST /driver/shift/payments` | `{"method":"cash|card","card_type":"debit|credit","idempotency_key":"<clave>"}`. `card_type` solo se envía para tarjeta. | Recibo del pago y viaje, con identificadores, medio, importe, saldo y fecha. |
| RF-07 | `frontend/conductor.html` — Cerrar turno | `POST /driver/shift/close` | `{"cash_counted":<efectivo contado>}` | `closed` y el resumen final `shift`, incluidos `cash_counted` y `cash_difference`. |

## Datos de apoyo compartidos

La interfaz carga `GET /routes` y `GET /fares/current` para mostrar rutas y calcular una referencia de tarifa. La API calcula y confirma el importe definitivo al registrar el pago. Los endpoints de conductor requieren el rol `DRIVER`; los endpoints de cuenta e historial requieren una sesión autenticada.

## Ubicación de la implementación

- Pantalla de acceso y registro: [`frontend/login.html`](../../frontend/login.html), lógica en [`frontend/login.js`](../../frontend/login.js) y estilos en [`frontend/login.css`](../../frontend/login.css).
- Entrada y selección del espacio: [`frontend/index.html`](../../frontend/index.html) y [`frontend/index.js`](../../frontend/index.js).
- Espacios por perfil: [`frontend/pasajero.html`](../../frontend/pasajero.html), [`frontend/conductor.html`](../../frontend/conductor.html), plantilla compartida [`frontend/workspace.html`](../../frontend/workspace.html), y lógica en [`frontend/app.js`](../../frontend/app.js).
- Cliente HTTP compartido: [`frontend/api.js`](../../frontend/api.js).
- Controladores y DTOs que definen las rutas y formas JSON: `backend/app/controllers/` y `backend/app/dtos/`.
