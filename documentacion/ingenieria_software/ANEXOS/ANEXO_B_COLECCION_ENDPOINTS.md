# ANEXO B. ENDPOINTS PRINCIPALES

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/api/v1/health` | No | Estado servicio |
| GET | `/api/v1/ready` | No | Estado BD |
| POST | `/api/v1/auth/login` | No | Login |
| POST | `/api/v1/auth/register` | No | Registro pasajero |
| GET | `/api/v1/auth/me` | Sí | Usuario actual |
| GET | `/api/v1/routes` | No | Listado rutas |
| GET | `/api/v1/routes/{id}/fares` | No | Tarifas vigentes |
| POST | `/api/v1/demo/account/top-ups` | Sí | Recarga |
| POST | `/api/v1/demo/account/payments` | Sí | Pago efectivo/tarjeta |
| POST | `/api/v1/demo/account/qr/validate` | Sí | Pago QR con saldo |
| GET | `/api/v1/payments/history` | Sí | Historial pagos |
| GET | `/api/v1/trips` / `/api/v1/demo/account/trips` | Sí | Historial viajes |
| GET | `/api/v1/trips/{id}` | Sí | Detalle viaje |
| POST | `/api/v1/transfers` | Sí | Crear transbordo |
| GET | `/api/v1/driver/demo/assignment` | Sí(DRIVER) | Asignación conductor |
| POST | `/api/v1/driver/shift/start` | Sí(DRIVER) | Iniciar turno |
| POST | `/api/v1/driver/shift/qr` | Sí(DRIVER) | Generar/renovar QR |
| POST | `/api/v1/driver/shift/close` | Sí(DRIVER) | Cerrar turno |
| GET | `/api/v1/admin/demo/metrics` | Sí | Métricas demo |
| POST | `/api/v1/admin/demo/reset` | Sí | Reset demo |
