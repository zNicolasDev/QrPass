# Flujo verificable de acciones — QrPass

Cada acción del sistema sigue el flujo:

**Pantalla → JavaScript → API (HTTP) → Backend (Controller → Service) → Base de datos (SQLite) → Respuesta**

Nada se resuelve solo en el frontend: el backend valida las reglas de negocio y la base de datos es la única fuente de verdad.

## Autenticación y sesión

| Acción | Pantalla | Función JS | Endpoint | Servicio backend | Tablas DB | Respuesta |
|---|---|---|---|---|---|---|
| Iniciar sesión | `login.html` | `loginForm.submit` | `POST /api/v1/auth/login` | `autenticar_usuario` | `users`, `user_roles`, `roles` | Token JWT + roles |
| Crear cuenta | `login.html` | `registrationForm.submit` | `POST /api/v1/auth/register` | `registrar_usuario` | `users`, `user_roles` | Confirmación + auto-login |
| Validar sesión al cargar | `pasajero.html` / `conductor.html` | `bootstrapAuthentication()` | `GET /api/v1/auth/me` | `obtener_usuario_activo` | `users`, `user_roles` | Usuario + roles (401 → logout) |
| Cerrar sesión | cualquier | `logout()` | (sin llamada; limpia token local) | — | — | Redirige a `login.html` |

## Catálogo y tarifa (lectura)

| Acción | Pantalla | Función JS | Endpoint | Servicio backend | Tablas DB | Respuesta |
|---|---|---|---|---|---|---|
| Cargar rutas | panel | `refreshPassengerData()` | `GET /api/v1/routes` | `listar_rutas_activas` | `routes` | Lista de rutas activas |
| Tarifa vigente | panel | `refreshPassengerData()` | `GET /api/v1/fares/current` | `obtener_tarifa_vigente` | `fares`, `routes` | Tarifa por ruta/día/destino |
| Hora oficial | panel conductor | `syncServerTime()` | `GET /api/v1/time` | `obtener_hora_servidor` | — | Hora del servidor |

## Pasajero — billetera y viajes

| Acción | Pantalla | Función JS | Endpoint | Servicio backend | Tablas DB | Respuesta |
|---|---|---|---|---|---|---|
| Consultar saldo | Resumen | `refreshPassengerData()` | `GET /api/v1/account` | `consultar_cuenta` | `users` | Saldo disponible |
| Recargar saldo | Recarga / modal rápido | `topUp()` | `POST /api/v1/account/top-ups` | `crear_recarga` | `payments` | Recibo + saldo |
| Pagar pasaje (efectivo/tarjeta) | Modal pago | `payment-form.submit` | `POST /api/v1/account/payments` | `crear_pago` | `payments`, `trips`, `fares` | Recibo + viaje + saldo |
| Pagar pasaje (QR/saldo) | Escanear QR | `passenger-qr-form.submit` | `POST /api/v1/account/qr/validate` | `validar_qr_pasajero` | `qr_codes`, `payments`, `trips` | Recibo + viaje + saldo |
| Traspasar pago de ruta | Modal traspaso | `transfer-form.submit` | `POST /api/v1/account/transfers` | `crear_transbordo` | `transfers`, `trips` | Recibo de traspaso |
| Historial de viajes | Mis viajes | `refreshPassengerData()` | `GET /api/v1/trips` | `listar_viajes` | `trips`, `routes`, `fares` | Lista de viajes |
| Historial de pagos | Mis viajes | `refreshPassengerData()` | `GET /api/v1/payments/history` | `listar_historial_pagos` | `payments`, `trips` | Movimientos unificados |
| Detalle de movimiento | Modal detalle | `openMovementDetails()` | (sin llamada; usa estado cargado) | — | — | — |
| Aviso de privacidad / plataforma | Modales | `openPrivacyInfo()` / `openPlatformInfo()` | (informativo) | — | — | — |
| Métricas globales (admin) | Modal plataforma | `openGlobalMetrics()` | `GET /api/v1/admin/metrics` | `consultar_metricas` | (agregados) | Totales de recaudo |

## Conductor — turno y recaudo

| Acción | Pantalla | Función JS | Endpoint | Servicio backend | Tablas DB | Respuesta |
|---|---|---|---|---|---|---|
| Consultar asignación(es) | Mi turno | `refreshDriverAssignments()` | `GET /api/v1/driver/assignment` y `GET /api/v1/driver/assignments` | `obtener_datos_asignacion_conductor` / `obtener_asignaciones_conductor` | `shifts`, `routes`, `vehicles` | Ruta(s) + vehículo + estado |
| Iniciar turno | Mi turno (sin activo) | `startDriverShift()` | `POST /api/v1/driver/shift/start?route_id=` | `iniciar_turno_conductor` | `shifts` (estado active) | Turno activo + totales |
| Consultar turno activo | Mi turno | `refreshDriverShift()` | `GET /api/v1/driver/shift` | `resumir_turno_conductor` | `shifts`, `payments`, `trips` | Totales por medio + movimientos |
| Generar QR del bus | Mi turno | `syncBusQr()` / `refresh-bus-qr` | `POST /api/v1/driver/shift/qr` | `crear_qr_turno_conductor` | `qr_codes`, `shifts` | Token + imagen QR + vencimiento |
| Registrar pago (efectivo/tarjeta) | Mi turno | `recordDriverPayment()` | `POST /api/v1/driver/shift/payments` | `registrar_pago_conductor` | `payments`, `trips`, `shifts` | Recibo de pago |
| Cerrar turno | Mi turno | `closeDriverShift()` | `POST /api/v1/driver/shift/close` | `cerrar_turno_conductor` | `shifts` (estado closed) | Resumen + diferencia de efectivo |
| Historial de turnos | Mi turno | `refreshDriverShiftHistory()` | `GET /api/v1/driver/shifts/history` | `consultar_historial_turnos` | `shifts` | Últimos cierres |

## Sistema

| Acción | Pantalla | Función JS | Endpoint | Servicio backend | Tablas DB | Respuesta |
|---|---|---|---|---|---|---|
| Health check | — | (infra) | `GET /api/v1/health` | `verificar_salud` | — | Estado del servicio |
| Ready check | — | (infra) | `GET /api/v1/ready` | `verificar_disponibilidad` | DB | Disponibilidad de BD |

## Reglas de diseño que garantizan el flujo

1. **Ninguna acción muta estado en el frontend sin llamar a la API** (saldo, viajes, turnos, pagos, QR, traspasos).
2. **El backend re-valida** reglas de negocio (saldo, tarifa, idempotencia, propiedad del turno, tiempo de traspaso, etc.) aunque el frontend también las verifique para UX.
3. **La DB es la única fuente de verdad**; el frontend solo refleja lo que el backend confirma.
4. **Seguridad por capas**: token firmado → `obtener_usuario_autenticado` → `requerir_rol` → servicio → DB. Cada endpoint protegido exige rol (`PASSENGER`, `DRIVER`, `ADMIN`).
5. **Sin datos quemados**: rutas/tarifas se importan del catálogo; conductores y administradores se crean por CLI/administración; montos de recarga son sugerencias de UI validadas por el backend.
6. **Separación por capas**: controller (HTTP) → service (reglas) → ORM (DB). Los controladores no acceden a la base de datos directamente.
