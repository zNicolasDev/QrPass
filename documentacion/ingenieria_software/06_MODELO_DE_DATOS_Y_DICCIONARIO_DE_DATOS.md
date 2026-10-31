# 6. MODELO DE DATOS Y DICCIONARIO DE DATOS

## 6.1. Modelo Físico
Basado en `backend/app/models/`. Tablas principales: `users`, `roles`, `user_roles`, `drivers`, `companies`, `vehicles`, `routes`, `fares`, `shifts`, `qr_codes`, `payments`, `trips`, `transfers`, `cards`, `boarded_devices`, `offline_syncs`. Ver `documentacion/diagramas/01_diagrama_er.md`.

## 6.2. Diccionario de Datos Clave

### users
| Campo | Tipo | Restricción | Descripción |
|---|---|---|---|
| id | INTEGER | PK | Identificador |
| names | VARCHAR(120) | NOT NULL | Nombres completos |
| username | VARCHAR(80) | UNIQUE NULL | Usuario |
| email | VARCHAR(254) | UNIQUE NULL | Correo |
| password_hash | VARCHAR(256) | NULL | Hash contraseña |
| privacy_consent_at | DATETIME(tz) | NULL | Consentimiento |
| document_number | VARCHAR(40) | UNIQUE NOT NULL | Documento |
| wallet_balance | INTEGER | NOT NULL DEFAULT 0, CHECK >=0 | Saldo |
| status | VARCHAR(20) | NOT NULL DEFAULT 'active' | Estado |

### payments
| Campo | Tipo | Restricción | Descripción |
|---|---|---|---|
| id | INTEGER | PK | Identificador |
| user_id | INTEGER | FK(users.id) NOT NULL | Propietario |
| idempotency_key | VARCHAR(80) | NULL | Clave idempotencia |
| card_id | INTEGER | FK(cards.id) NULL | Tarjeta |
| qr_code_id | INTEGER | FK(qr_codes.id) NULL | QR usado |
| method | VARCHAR(20) | NOT NULL | `cash`, `card_debit`, `card_credit`, `wallet`, `top_up` |
| movement_type | VARCHAR(20) | NOT NULL | `fare_payment`, `top_up` |
| amount | INTEGER | NOT NULL CHECK>=0 | Monto |
| balance_before | INTEGER | NOT NULL CHECK>=0 | Saldo antes |
| balance_after | INTEGER | NOT NULL CHECK>=0 | Saldo después |
| status | VARCHAR(20) | NOT NULL DEFAULT 'completed' | Estado |
| created_at | DATETIME(tz) | NOT NULL | Creación |

Restricciones: `ck_payments_*_nonnegative`, `uq_payments_user_idempotency_key(user_id,idempotency_key)`

### trips
| Campo | Tipo | Restricción | Descripción |
|---|---|---|---|
| id | INTEGER | PK | Identificador |
| payment_id | INTEGER | FK(payments.id) UNIQUE NOT NULL | Pago asociado |
| shift_id | INTEGER | FK(shifts.id) NULL | Turno |
| fare_id | INTEGER | FK(fares.id) NOT NULL | Tarifa |
| route_id | INTEGER | FK(routes.id) NOT NULL | Ruta |
| created_at | DATETIME(tz) | NOT NULL | Fecha/hora |

### qr_codes
| Campo | Tipo | Restricción | Descripción |
|---|---|---|---|
| id | INTEGER | PK | Identificador |
| shift_id | INTEGER | FK(shifts.id) NOT NULL | Turno |
| token | VARCHAR | UNIQUE NOT NULL | Token firmado |
| expires_at | DATETIME(tz) | NOT NULL | Expiración |
| used_at | DATETIME(tz) | NULL | Uso |
| created_at | DATETIME(tz) | NOT NULL | Creación |

### transfers
| Campo | Tipo | Restricción | Descripción |
|---|---|---|---|
| id | INTEGER | PK | Identificador |
| origin_trip_id | INTEGER | FK(trips.id) UNIQUE NOT NULL | Viaje origen |
| destination_trip_id | INTEGER | FK(trips.id) UNIQUE NOT NULL | Viaje destino |
| applied_at | DATETIME(tz) | NOT NULL | Aplicación |

### fares
| Campo | Tipo | Restricción | Descripción |
|---|---|---|---|
| id | INTEGER | PK | Identificador |
| route_id | INTEGER | FK(routes.id) NOT NULL | Ruta |
| day_type | VARCHAR(20) | NOT NULL | `weekday`/`weekend` |
| destination | VARCHAR(80) | NULL | Destino |
| amount | INTEGER | NOT NULL | Valor |
| active | BOOLEAN | NOT NULL DEFAULT TRUE | Vigente |
