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
| GET | `/account` | Billetera |
| GET | `/payments/history` | Historial unificado |
| GET | `/trips` | Viajes del usuario |
| GET | `/trips/{trip_id}` | Detalle de viaje |
| POST | `/account/qr/validate` | Escaneo de QR del bus |
| POST | `/account/payments` | Pago en efectivo o tarjeta |
| POST | `/account/top-ups` | Recarga |
| POST | `/account/transfers` | Traspaso |
| GET | `/admin/metrics` | Métricas globales (ADMIN) |
| GET | `/driver/assignment` | Asignación (DRIVER) |
| GET | `/driver/shift` | Turno activo |
| GET | `/driver/shifts/history` | Historial de cierres |
| POST | `/driver/shift/start` | Inicio de turno |
| POST | `/driver/shift/payments` | Registro de pago |
| POST | `/driver/shift/qr` | Generación de QR |
| POST | `/driver/shift/close` | Cierre de turno |