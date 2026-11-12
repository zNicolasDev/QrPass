# Anexo E. Contrato de integración por requerimiento funcional

El contrato describe la relación entre cada requerimiento funcional y el endpoint, la solicitud y la respuesta esperada. Sigue el flujo: pantalla → JavaScript → API → backend → base de datos.

| RF | Acción en pantalla | Endpoint | Solicitud (ejemplo) | Respuesta (ejemplo) |
|---|---|---|---|---|
| RF-01 | Formulario de registro | `POST /api/v1/auth/register` | `{"names":"Ana","email":"ana@x.com","password":"Clave-Segura-2026","privacy_consent":true}` | `{"user_id":..., "username":"ana@x.com","roles":["PASSENGER"]}` |
| RF-05 | Botón pagar en efectivo | `POST /api/v1/account/payments` | `{"route_id":1,"method":"cash"}` | `{"payment_id":..,"amount":3300,"wallet_balance":50000,"status":"completed"}` |
| RF-06 | Escaneo de QR | `POST /api/v1/account/qr/validate` | `{"token":"...","idempotency_key":"k"}` | `{"payment_id":..,"amount":3300,"wallet_balance":46700}` |
| RF-04 | Campo de monto | `POST /api/v1/account/top-ups` | `{"amount":10000,"idempotency_key":"k"}` | `{"payment_id":..,"amount":10000,"wallet_balance":60000}` |

## Códigos HTTP

- `200`/`201`: éxito.
- `400`/`422`: error de validación (entrada inválida).
- `401`: no autenticado.
- `403`: sin permiso.
- `404`: recurso no encontrado.
- `409`: conflicto (idempotencia, saldo insuficiente).
- `410`: QR expirado.
- `500`: error interno.
- `503`: servicio no disponible.

## Manejo de errores

Toda solicitud recibe una respuesta JSON con `detail` explicando el motivo. Los mensajes se redactan de forma intuitiva para usuarios no expertos (por ejemplo, "El monto debe ser mayor a cero"). La validación rechaza valores inválidos como recargas negativas.