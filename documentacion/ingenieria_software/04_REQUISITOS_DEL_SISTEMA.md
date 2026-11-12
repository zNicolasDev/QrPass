# 5. Requisitos del sistema

## 5.1 Requisitos funcionales

**Tabla 1. Requisitos funcionales del sistema.**

| ID | Descripción | Endpoint principal |
|---|---|---|
| RF-01 | Registro y autenticación de pasajero | `POST /api/v1/auth/register`, `POST /api/v1/auth/login` |
| RF-02 | Consulta de identidad y roles | `GET /api/v1/auth/me` |
| RF-03 | Billetera y saldo | `GET /api/v1/account` |
| RF-04 | Recarga idempotente | `POST /api/v1/account/top-ups` |
| RF-05 | Pago manual (efectivo/tarjeta) | `POST /api/v1/account/payments` |
| RF-06 | Pago mediante QR del bus | `POST /api/v1/account/qr/validate` |
| RF-07 | Traspaso a otra ruta (≤ 20 min) | `POST /api/v1/account/transfers` |
| RF-08 | Historial de viajes y movimientos | `GET /api/v1/trips`, `GET /api/v1/payments/history` |
| RF-09 | Tarifa vigente por ruta y día | `GET /api/v1/fares/current` |
| RF-10 | Gestión de turno del conductor | `POST /api/v1/driver/shift/start`, `GET /api/v1/driver/shift` |
| RF-11 | Generación de QR del turno | `POST /api/v1/driver/shift/qr` |
| RF-12 | Registro de pagos del conductor | `POST /api/v1/driver/shift/payments` |
| RF-13 | Cierre y conciliación de turno | `POST /api/v1/driver/shift/close` |
| RF-14 | Estado del servicio | `GET /api/v1/health`, `GET /api/v1/ready` |

### 5.1.1 Descripción detallada de requisitos funcionales

- **RF-01:** El sistema debe permitir el registro de pasajeros con nombres, correo y contraseña. El correo debe ser único y la contraseña tener al menos 12 caracteres.
- **RF-04:** La recarga debe ser idempotente mediante clave; montos entre $1 y $500.000.
- **RF-06:** El QR debe estar firmado con HMAC, vencer en 15 minutos y asociarse al turno activo.
- **RF-07:** El traspaso solo se permite una vez por viaje, entre rutas distintas y dentro de 20 minutos.
- **RF-09:** La tarifa depende de la ruta, el destino y el tipo de día; los valores se importan desde el catálogo maestro de rutas y tarifas.
- **RF-13:** El cierre de turno consolida efectivo, QR y tarjeta, y calcula la diferencia.

## 5.2 Requisitos no funcionales

**Tabla 2. Requisitos no funcionales del sistema.**

| ID | Descripción | Verificación |
|---|---|---|
| RNF-01 | Tiempo de respuesta < 1,5 s en operaciones críticas | Pruebas de carga (pendiente) |
| RNF-02 | Propiedades ACID en transacciones | `test_failed_payment_commit_rolls_back...` |
| RNF-03 | Cifrado de credenciales (hash) | Inspección de código |
| RNF-04 | Validación de entrada mediante DTOs | Pruebas de validación |
| RNF-05 | Disponibilidad verificable | `test_readiness_checks_database...` |
| RNF-06 | Interfaz adaptable y PWA | Revisión manual |
| RNF-07 | Mensajes de error intuitivos | Revisión de UX |

## 5.3 Reglas de negocio

**Tabla 3. Reglas de negocio.**

| ID | Regla | Implementación |
|---|---|---|
| RN-01 | Saldo nunca negativo | `CheckConstraint` + servicio |
| RN-02 | Recargas > 0 y ≤ $500.000 | DTO `CrearRecargaSolicitud` |
| RN-03 | Idempotencia de pagos | Clave única por usuario |
| RN-04 | QR válido 15 min y firmado | `servicios/qr.py` |
| RN-05 | Un pasajero no paga dos veces con el mismo QR | Consumo de QR |
| RN-06 | Traspaso ≤ 20 min y rutas distintas | `servicios/transbordos.py` |
| RN-07 | Tarifa dinámica por día | `servicios/rutas_tarifas.py` |
| RN-08 | Pago con saldo requiere QR | Validación en servicio |
| RN-09 | Cuentas nuevas solo pasajero | `registrar_pasajero` |
| RN-10 | Toda solicitud recibe respuesta HTTP | Handlers globales |

## Referencias

- Pressman, R. S., & Maxim, B. R. (2020). *Software engineering: A practitioner's approach* (9.ª ed.). McGraw-Hill.
- Sommerville, I. (2016). *Software engineering* (10.ª ed.). Pearson.