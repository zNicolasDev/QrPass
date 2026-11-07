# Anexo B. Colección de endpoints

Todos los endpoints usan el prefijo `/api/v1`.

| Método | Endpoint | Función |
|---|---|---|
| GET | `/health` | Estado del servicio |
| GET | `/ready` | Disponibilidad con `SELECT 1` |
| GET | `/routes` | Catálogo de rutas |
| GET | `/fares/current` | Tarifa vigente |
| POST | `/auth/register` | Registro de pasajero |
| POST | `/auth/login` | Inicio de sesión |
| GET | `/auth/me` | Identidad y roles |
| GET | `/demo/account` | Billetera |
| GET | `/demo/account/trips` | Historial de viajes |
| GET | `/payments/history` | Historial unificado |
| GET | `/trips` | Viajes del usuario |
| GET | `/trips/{trip_id}` | Detalle de viaje |
| POST | `/demo/account/qr/validate` | Escaneo de QR del bus |
| POST | `/demo/account/payments` | Pago simulado |
| POST | `/demo/account/top-ups` | Recarga |
| POST | `/demo/account/transfers` | Traspaso |
| GET | `/driver/demo/assignment` | Asignación (DRIVER) |
| GET | `/driver/shift` | Turno activo |
| GET | `/driver/shifts/history` | Historial de cierres |
| POST | `/driver/shift/start` | Inicio de turno |
| POST | `/driver/shift/payments` | Registro de pago |
| POST | `/driver/shift/qr` | Generación de QR |
| POST | `/driver/shift/close` | Cierre de turno |