# Anexo F. Diccionario de datos (resumen)

| Tabla | Columna | Tipo | Restricción | Descripción |
|---|---|---|---|---|
| users | id | INTEGER | PK | Identificador del usuario |
| users | names | VARCHAR(120) | NOT NULL | Nombres de la persona |
| users | username | VARCHAR(80) | UNIQUE | Usuario de acceso |
| users | email | VARCHAR(254) | UNIQUE | Correo electrónico |
| users | password_hash | VARCHAR(256) | NULL | Hash de contraseña |
| users | document_number | VARCHAR(40) | NOT NULL, UNIQUE | Documento |
| users | wallet_balance | INTEGER | NOT NULL, ≥ 0 | Saldo en COP |
| users | status | VARCHAR(20) | NOT NULL | Estado de la cuenta |
| users | privacy_consent_at | DATETIME(tz) | NULL | Consentimiento |
| routes | id | INTEGER | PK | Identificador de ruta |
| routes | name | VARCHAR | NOT NULL | Nombre de ruta |
| routes | is_active | BOOLEAN | NOT NULL | Ruta activa |
| fares | id | INTEGER | PK | Identificador de tarifa |
| fares | route_id | INTEGER | FK | Ruta asociada |
| fares | destination | VARCHAR | NULL | Destino |
| fares | amount | INTEGER | NOT NULL | Monto en COP |
| fares | day_type | VARCHAR | NOT NULL | hábil/fin de semana |
| payments | id | INTEGER | PK | Identificador de pago |
| payments | user_id | INTEGER | FK | Usuario |
| payments | movement_type | VARCHAR | NOT NULL | fare_payment/top_up |
| payments | method | VARCHAR | NOT NULL | cash/card/wallet/qr |
| payments | amount | INTEGER | NOT NULL | Monto |
| payments | balance_before | INTEGER | NOT NULL | Saldo anterior |
| payments | balance_after | INTEGER | NOT NULL | Saldo posterior |
| payments | status | VARCHAR | NOT NULL | Estado |
| payments | idempotency_key | VARCHAR | UNIQUE (parcial) | Clave de idempotencia |
| trips | id | INTEGER | PK | Identificador de viaje |
| trips | payment_id | INTEGER | FK, UNIQUE | Pago asociado |
| trips | route_id | INTEGER | FK | Ruta |
| trips | fare_id | INTEGER | FK | Tarifa |
| shifts | id | INTEGER | PK | Identificador de turno |
| shifts | driver_id | INTEGER | FK | Conductor |
| shifts | route_id | INTEGER | FK | Ruta |
| shifts | status | VARCHAR | NOT NULL | active/closed |
| qr_codes | id | INTEGER | PK | Identificador QR |
| qr_codes | token | VARCHAR | NOT NULL | Token firmado |
| qr_codes | expires_at | DATETIME | NOT NULL | Vencimiento |
| transfers | id | INTEGER | PK | Identificador de traspaso |
| transfers | origin_trip_id | INTEGER | FK | Viaje origen |
| transfers | destination_route_id | INTEGER | FK | Ruta destino |