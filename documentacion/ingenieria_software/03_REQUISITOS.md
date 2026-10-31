# 3. REQUISITOS DEL SISTEMA

## 3.1. Requisitos Funcionales (RF)

| ID | Requisito | Prioridad | Estado |
|---|---|---|---|
| RF-01 | El sistema debe permitir iniciar sesión con usuario y contraseña. | Alta | Implementado |
| RF-02 | El sistema debe permitir registrar un pasajero con consentimiento de privacidad. | Alta | Implementado |
| RF-03 | El sistema debe asignar roles `PASSENGER`/`DRIVER` según el caso. | Alta | Implementado |
| RF-04 | El pasajero debe poder recargar saldo con clave de idempotencia. | Alta | Implementado |
| RF-05 | El pasajero debe poder pagar pasaje en efectivo o con tarjeta. | Alta | Implementado |
| RF-06 | El pasajero debe poder pagar con saldo escaneando el QR del bus. | Alta | Implementado |
| RF-07 | El conductor debe poder iniciar/cerrar turno y generar QR firmado. | Alta | Implementado |
| RF-08 | El sistema debe validar QR por firma, vigencia, uso único, turno y ruta. | Alta | Implementado |
| RF-09 | El sistema debe calcular tarifa según ruta, tipo de día y destino cuando aplique. | Alta | Implementado |
| RF-10 | El pasajero debe poder consultar historial de pagos y viajes propios. | Alta | Implementado |
| RF-11 | El sistema debe soportar transbordos con ventana de 20 minutos. | Alta | Implementado |
| RF-12 | El sistema debe garantizar idempotencia en recargas y pagos. | Alta | Implementado |
| RF-13 | El sistema debe exponer catálogo de rutas, tarifas y estado del servicio. | Media | Implementado |

## 3.2. Requisitos No Funcionales (RNF)

| ID | Requisito | Categoría | Estado |
|---|---|---|---|
| RNF-01 | Arquitectura por capas (Controladores/Servicios/Modelos/DTOs). | Arquitectura | Implementado |
| RNF-02 | Validación de datos con Pydantic v2. | Integridad | Implementado |
| RNF-03 | Autenticación basada en token Bearer. | Seguridad | Implementado |
| RNF-04 | Hashing de contraseñas. | Seguridad | Implementado |
| RNF-05 | Integridad referencial con Foreign Keys (SQLite). | Integridad | Implementado |
| RNF-06 | Uso de transacciones para operaciones atómicas. | Confiabilidad | Implementado |
| RNF-07 | Respuestas consistentes con `response_model`. | Mantenibilidad | Implementado |
| RNF-08 | Soporte para pruebas con `TestClient` y BD en memoria. | Testeabilidad | Implementado |
| RNF-09 | PWA con Service Worker para caché de recursos. | Usabilidad/Disponibilidad | Implementado |
| RNF-10 | CORS configurado por variable de entorno. | Configurabilidad | Implementado |

## 3.3. Reglas de Negocio (RN)

| ID | Regla | Descripción |
|---|---|---|
| RN-01 | Saldo no negativo | `Usuario.saldo_billetera >= 0`. |
| RN-02 | Pagos con saldo solo por QR | En pagos manuales, `medio = wallet` no está permitido. |
| RN-03 | Tarjeta requiere tipo | Si `medio = card`, debe indicarse `card_type` (`debit`/`credit`). |
| RN-04 | Destino obligatorio cuando aplique | Rutas con destinos configurados exigen `destination`. |
| RN-05 | Un viaje por pago | `Viaje.payment_id` es único. |
| RN-06 | Idempotencia por usuario | Único (`user_id`, `idempotency_key`) en pagos. |
| RN-07 | QR de un solo uso | Se marca `CodigoQr.usado_en` al validar. |
| RN-08 | QR firmado y vigente | Debe pertenecer a turno activo, no expirado, correspondiente a ruta/conductor. |
| RN-09 | Transbordo ventana 20 min | Debe aplicarse dentro de los 20 minutos desde el viaje origen. |
| RN-10 | Saldo suficiente para QR | Se valida antes de descontar y crear viaje/pago. |
