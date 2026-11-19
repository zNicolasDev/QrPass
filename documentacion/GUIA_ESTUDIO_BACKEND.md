# Guía de estudio: backend de QrPass

Material para entender y defender el backend ante preguntas técnicas. Está escrito para
alguien que va a responder en voz alta, no para leer en silencio.

---

## 1. El mapa en 30 segundos

El backend es un restaurante:

| Parte del restaurante | Parte del código | Qué hace |
|---|---|---|
| Cliente que pide | `frontend/app.js` | Manda peticiones HTTP |
| Mesero | `app/controllers/` | Recibe el pedido y decide a quién pasarlo |
| Cocina | `app/servicios/` | Aquí están las reglas de negocio |
| Despensa | `app/models/` | Tablas de SQLite |
| Plato servido | `app/dtos/` | Forma exacta del JSON que sale |
| Llave y registro | `app/seguridad/` | Tokens, contraseñas y QR firmados |

Frase para memorizar: **los controladores hablan HTTP, los servicios deciden, los modelos
guardan, los DTOs presentan.**

El archivo que arma todo es `backend/app/core/main.py` → `crear_aplicacion()`.

---

## 2. Las capas, una por una

### Arranque (`core/main.py`)

- Crea la base, guarda el secreto en `app.state`, registra los manejadores de error y mete los routers.
- Al iniciar llama `database.initialize()`: crea tablas, aplica dos arreglos viejos de SQLite e inserta los roles `PASSENGER` y `DRIVER`.
- Si `QR_PASS_SERVE_FRONTEND=1`, también sirve el frontend desde la misma API.
- CORS: sin variable configurada, `*` en desarrollo y `[]` en producción. Solo `GET` y `POST`.

### Controladores (`controllers/`)

- `sistema.py`: `health`, `ready`, `time`, `routes`, `fares/current`.
- `autenticacion.py`: `register`, `login`, `me`.
- `conductor.py`: `assignment`, `assignments`, `shift`, `shift/start`, `shift/qr`, `shift/payments`, `shift/close`, `shifts/history`.
- `pasajero.py`: cuenta, pagos, recargas, transbordos e historiales.

### Servicios (`servicios/`)

`usuarios.py`, `pagos.py`, `qr.py`, `turnos.py`, `transbordos.py`, `rutas_tarifas.py`,
`catalogo.py`, `viajes.py`, `comun.py`.

Si algo no debería pasar, se lanza `ErrorDominio(código, mensaje)` y el handler lo convierte
en JSON con `{"detail": "..."}`.

### Modelos (`models/`)

16 tablas: `users`, `roles`, `user_roles`, `drivers`, `transport_companies`, `vehicles`,
`boarding_devices`, `routes`, `fares`, `shifts`, `cards`, `qr_codes`, `payments`, `trips`,
`transfers`, `offline_syncs`.

Truco: **Python en español, columnas en inglés**. `Usuario.saldo_billetera` → columna
`wallet_balance`. Las relaciones usan `back_populates` y no declaran `lazy`: rige el default
de SQLAlchemy.

Los estados son cadenas, no enums de base de datos: `assigned → active → closed` en turnos,
`active → revoked/consumed` en QR, `completed` en pagos.

### DTOs (`dtos/`)

Igual que los modelos: campo en español, alias en inglés. `monto` se serializa como `amount`.
Configuración: `from_attributes=True`, `populate_by_name=True`, `serialize_by_alias=True`.

Un validador global convierte todas las fechas a **America/Bogota (-05:00)**. Las fechas de
SQLite vienen sin zona y se interpretan como UTC antes de convertir.

Solo existen dos enums Python: `MedioPago` (`wallet`, `cash`, `card`) y `TipoTarjeta`
(`debit`, `credit`).

### Catálogo maestro

No hay archivo de catálogo en el repositorio. Los roles, los perfiles de roles, las 32 rutas y
las tarifas viven en la tabla `app_config` de `qrpass.db`. La tarifa ordinaria es **3300 en
weekday** y **3400 en weekend**; la ruta **48** tiene destinos y Juntas cuesta **3800/3900**.

Se cargan una sola vez con `python -m app.management load-catalog --archivo <catalogo.json>` y
se aplican a las tablas con `python -m app.management import-catalog`. La API solo lee la base
de datos.

---

## 3. Los tres flujos que sí o sí debes saber

### A. Registro y login

1. `register`: email a minúsculas, nombre colapsado, contraseña mínimo **12 caracteres**,
   consentimiento `true` obligatorio, rol `PASSENGER`, saldo **0**, documento `QRPASS-<hex>`.
2. La contraseña se guarda con **PBKDF2**, nunca en texto.
3. `login` usa el mismo mensaje para usuario inexistente y contraseña mala:
   **"Usuario o contraseña incorrectos."** Así no se filtra información.
4. Token propio: `<payload_base64url>.<firma_base64url>`, HMAC-SHA256 con
   `QR_PASS_AUTH_SECRET`, duración **3600 s**. El token solo lleva `sub` y `exp`:
   **los roles se consultan en la BD**, no se confían al token.

### B. El QR del bus (el corazón)

1. El conductor **inicia turno** (`POST /driver/shift/start?route_id=X`): `assigned` pasa a `active`.
2. `POST /driver/shift/qr` genera `QRP1.<payload>.<firma_hex>` con claims `v=1`,
   `kind=bus_boarding`, `qr_id`, `sub`, `route_id`, `shift_id`, `exp` y `jti`.
   Vigencia: **60 segundos**. Sin `renew=true`, se reutiliza el QR vigente.
3. El pasajero escanea y llama `POST /account/qr/validate` con `token`, `idempotency_key` y
   `destination`.
4. El servicio valida: prefijo y firma → expiración (**410**) → QR `active` en BD → turno
   activo → ruta y tarifa → destino → saldo → idempotencia.
5. Éxito: descuenta billetera con `UPDATE` condicional, marca el QR como `consumed`, crea
   `Pago` (`wallet`) y `Viaje` en **una sola transacción**. Si falla el commit, se revierte todo.

### C. Pagos, recargas y transbordos

- `cash`, `card_debit` y `card_credit` crean `Pago` + `Viaje`. `wallet` **solo** se puede pagar
  escaneando el QR del bus.
- En BD el medio se guarda como `cash`, `wallet`, `card_debit` o `card_credit`: el enum de
  entrada `card` se expande según el tipo de tarjeta.
- Recarga: monto **1 a 500.000**, idempotente por `(usuario, clave)`. Misma clave y mismo monto
  devuelve el mismo recibo; misma clave con otro monto da **409**.
- Transbordo: viaje propio, pagado, no transferido, **menos de 20 minutos**, ruta destino
  distinta y activa, cargo **$0**.

**Turnos:** `assigned → active → closed`. El cierre guarda el efectivo contado y la diferencia.
El historial devuelve los últimos **20**.

---

## 4. Chuleta de números

| Dato | Valor |
|---|---|
| QR del bus | 60 s |
| Token de sesión | 3600 s |
| Transbordo | 20 min |
| Recarga máxima | $500.000 |
| Idempotency key | 8–80 caracteres |
| Contraseña | 12–256 |
| Usuario | 3–254 |
| Nombres | 2–120 |
| Token QR en la request | 20–512 |
| Destino | 1–60 |
| Historial de turnos | 20 |
| Tarifa weekday / weekend | 3300 / 3400 |
| Zona horaria | America/Bogota (-05:00) |

**Pregunta trampa:** domingo o festivo colombiano = `weekend`. **Sábado = `weekday`**.

---

## 5. Errores: qué significa cada código

- **401** → token ausente, malo o vencido. `Autenticación requerida o sesión vencida.`
- **403** → token válido sin rol `DRIVER`. `Tu cuenta no tiene el rol requerido para esta operación.`
- **404** → no existe el viaje o la ruta, o no pertenece al usuario.
- **409** → conflicto de negocio: saldo insuficiente, QR ya usado, clave repetida, tiempo de transbordo vencido.
- **410** → el QR expiró; hay que escanear el nuevo.
- **422** → validación de entrada. El cuerpo trae `detail` y `errores[]` con `campo` y `mensaje`.
- **503** → base no disponible (`/ready`) o roles no inicializados.
- **500** → `Ocurrió un error inesperado. Intenta de nuevo en unos momentos.`

Orden de evaluación: **401 → 403 → 422 → lógica del servicio**. Por eso un endpoint de
conductor sin token y con body inválido devuelve 401, no 422.

---

## 6. Preguntas frecuentes, respondidas corto

**¿Por qué hay DTO si ya está el modelo?**
El modelo describe almacenamiento; el DTO describe el contrato. Así no se filtra `password_hash`
y se pueden aplanar respuestas, como `ReciboPago` (pago + viaje + ruta).

**¿Por qué el QR dura solo 60 s?**
Para que una captura no sirva de nuevo. El bus rota el código; para eso existe `renew=true`.

**¿El token guarda los roles?**
No. Se leen de `user_roles` en cada petición. Un cambio de rol surte efecto sin esperar a que
el token expire.

**¿Qué pasa si no hay `QR_PASS_AUTH_SECRET` en producción?**
La app no arranca. En desarrollo genera uno aleatorio, así que las sesiones mueren al reiniciar.
El secreto debe tener al menos 32 bytes.

**¿Por qué existen `assignment` y `assignments`?**
El frontend usa el plural para el selector de turnos. El singular se conserva como contrato
público y para las pruebas; además puede crear un turno asignado copiando el último cerrado.

**¿Por qué `/time` no lleva zona horaria?**
El frontend solo lo usa para calcular un desfase contra `Date.now()` y dibujar las cuentas
regresivas. Es hora local del servidor en ISO.

**¿Hay migraciones versionadas?**
No. Hay dos ajustes SQLite "in place" en `database.py`: `_upgrade_sqlite_user_columns` y
`_upgrade_sqlite_fare_destinations`. Es una limitación conocida.

**¿Hay datos quemados en el código?**
No. Rutas, tarifas, roles y la asignación de roles por perfil viven únicamente en la tabla
`app_config` de `qrpass.db`. El repositorio no versiona archivos de datos. Los únicos valores
fijos en Python son reglas de negocio (vigencias, límites y zona horaria), no datos maestros.

**¿Se guarda el número de tarjeta?**
No. Solo banco y tipo (`debit` / `credit`). El cobro es registro interno, sin pasarela.

**¿`offline_syncs` y `boarding_devices` están en uso?**
No implementan modo offline; son soporte para un flujo futuro.

---

## 7. Quiz de 15 preguntas

Responde en voz alta antes de mirar las respuestas.

1. ¿Cuánto dura el QR del bus?
2. ¿Cuánto dura el token de sesión?
3. ¿Sábado es `weekday` o `weekend`?
4. ¿Dónde se consultan los roles: en el token o en la base?
5. ¿Qué código HTTP devuelve un QR expirado?
6. ¿Cuál es la recarga máxima permitida?
7. ¿Qué medio de pago exige escanear el QR del bus?
8. ¿Cuántos minutos dura la ventana de transbordo?
9. ¿Cuántos turnos cerrados devuelve el historial?
10. ¿Qué tabla guarda el saldo de la billetera?
11. ¿Cómo se llama el helper que centraliza base64url?
12. ¿Qué pasa con el rollback si falla el commit al canjear un QR?
13. ¿Se puede pagar con tarjeta sin indicar débito o crédito?
14. ¿Qué hace `database.initialize()` además de crear tablas?
15. ¿Qué Colombia tiene que ver con las tarifas?

<details>
<summary>Respuestas</summary>

1. 60 segundos.
2. 3600 segundos (1 hora).
3. `weekday`. Solo domingo y festivos colombianos son `weekend`.
4. En la base de datos, tabla `user_roles`.
5. 410.
6. $500.000.
7. `wallet`.
8. 20 minutos.
9. 20.
10. `users`, columna `wallet_balance`.
11. `backend/app/seguridad/encoding.py`.
12. Se revierten el QR, el saldo, el pago y el viaje juntos; es una sola transacción.
13. No: `card_type` es obligatorio y da 422 si falta.
14. Aplica los dos upgrades de SQLite e inserta los roles `PASSENGER` y `DRIVER`.
15. El cálculo de `day_type` usa los festivos de Colombia para elegir tarifa.

</details>

---

## 8. Cómo estudiarlo en 20 minutos

1. Abre `core/main.py` y lee `crear_aplicacion()` de arriba abajo (5 min).
2. Abre `servicios/qr.py` y sigue `generar → validar → consumir` (7 min).
3. Abre `servicios/pagos.py` y `servicios/transbordos.py` (5 min).
4. Corre `cd backend && python -m pytest -q`: son **28 pruebas**. Cada nombre de test es una
   frase de estudio.
