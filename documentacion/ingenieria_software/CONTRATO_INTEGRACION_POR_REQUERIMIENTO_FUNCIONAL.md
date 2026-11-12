# Contrato de integración por requerimiento funcional: módulos de QrPass

Este documento afianza el contrato de integración del proyecto QrPass, una plataforma de recaudo electrónico para el transporte público de Ibagué. El contrato se organiza por requerimiento funcional y por subrequerimiento, de modo que cada fila conecta una acción de la interfaz con un método, un endpoint, una solicitud, una respuesta y un conjunto de errores. La primera parte explica qué es, para qué sirve, qué debe contener y cómo se elabora; la segunda parte presenta las tablas de los módulos 1 a 4 de la especificación de requisitos y un módulo complementario de administración.

## 1. ¿Qué es un contrato de integración por requerimiento funcional?

Es un acuerdo técnico y verificable entre el equipo que construye la interfaz, que actúa como consumidor, y el equipo que expone la API, que actúa como proveedor. Para cada requerimiento funcional (RF) y cada subrequerimiento, el contrato fija la pantalla y la acción que lo activan, el método HTTP, la ruta del endpoint, la estructura de la solicitud, la estructura de la respuesta, los códigos de error y las reglas de negocio que el servidor garantiza. No es una lista informal de rutas: es la especificación de una frontera entre componentes. Igual que una interfaz en el diseño orientado a objetos, oculta la implementación y obliga a que ambas partes utilicen el mismo lenguaje (Pressman & Maxim, 2020; Sommerville, 2016).

En el estilo arquitectónico REST, el contrato se construye alrededor de recursos, representaciones y una interfaz uniforme (Fielding, 2000). En las API HTTP, la especificación OpenAPI formaliza esa descripción para que personas y herramientas puedan descubrir y comprender el servicio sin leer su código fuente (OpenAPI Initiative, 2021).

## 2. ¿Para qué se elabora?

El contrato cumple una función de coordinación y de control. Sus propósitos principales son los siguientes:

- Eliminar suposiciones entre frontend y backend: cada campo, tipo, obligatoriedad y código de respuesta queda escrito antes de programar.
- Permitir el trabajo en paralelo: la interfaz puede construirse contra ejemplos y simulaciones mientras el backend implementa la operación real.
- Mantener la trazabilidad: cada subrequerimiento se conecta con una pantalla, un endpoint, una prueba y un caso de uso.
- Detectar brechas temprano: campos faltantes, permisos incorrectos, respuestas incompletas o códigos de error ambiguos se descubren en la revisión, no en la integración.
- Habilitar pruebas de contrato: un esquema OpenAPI o una prueba de contrato verifica que el proveedor siga cumpliendo lo acordado (Pact Foundation, 2026).
- Controlar cambios: toda modificación incompatible se identifica, se negocia y se versiona.
- Hacer explícitos la seguridad y las reglas del negocio: roles, propiedad de los datos, idempotencia, límites y transacciones.

## 3. ¿Qué debe llevar?

Un contrato completo debe contener, como mínimo, los siguientes elementos:

1. Identificación y control: nombre del proyecto, versión, fecha, autores, estado (borrador, revisado o aprobado) e historial de cambios.
2. Alcance: módulos, requerimientos y subrequerimientos incluidos, y lo que queda fuera.
3. Pantalla y acción: archivo o URL de la pantalla, vista, control que dispara la operación, rol del usuario y precondiciones.
4. Método y endpoint: verbo HTTP, ruta base versionada, recurso, parámetros de ruta y de consulta.
5. Autenticación y autorización: esquema, encabezado, roles permitidos y regla de propiedad del recurso.
6. Solicitud: encabezados, cuerpo, tipos, campos obligatorios y opcionales, restricciones, ejemplo y clave de idempotencia cuando aplique.
7. Respuesta: código de estado, cuerpo, ejemplo, significado de cada campo, unidades, moneda y formato de fechas.
8. Errores: códigos, estructura del mensaje, texto para la persona y acción de recuperación.
9. Reglas de negocio y efectos: validaciones, límites, transacciones, rollback y efectos secundarios.
10. Requisitos no funcionales: tiempo de respuesta, paginación, límites de uso y caché.
11. Trazabilidad y pruebas: RF, caso de uso, criterio de aceptación y prueba de contrato.
12. Versionado: política de cambios compatibles e incompatibles y periodo de transición.

## 4. ¿Cómo se elabora?

El contrato se construye de forma iterativa y conjunta. El procedimiento aplicado en QrPass fue el siguiente:

1. Inventariar los requerimientos funcionales y descomponerlos en subrequerimientos verificables.
2. Inventariar las pantallas y las acciones que cada subrequerimiento necesita.
3. Modelar los recursos y elegir los verbos HTTP; evitar rutas que describan acciones cuando el recurso puede nombrarse.
4. Definir los DTO de entrada y salida, con tipos, restricciones y ejemplos.
5. Definir respuestas, errores, autenticación y reglas de negocio.
6. Revisar el contrato en una sesión conjunta de frontend, backend y pruebas.
7. Congelar una versión y publicarla; en QrPass se mantiene como documento Markdown y la API expone `/docs` con OpenAPI.
8. Construir simulaciones y pruebas de contrato a partir de los ejemplos.
9. Implementar y verificar cada operación contra el contrato.
10. Registrar los cambios y versionar toda modificación incompatible.

## 5. ¿Por qué se hace de esta manera?

El enfoque se denomina API-first o contract-first: primero se acuerda la interfaz y después se implementa. Esta decisión reduce el acoplamiento oculto entre consumidor y proveedor, porque hace visibles las expectativas de ambas partes (Robinson, 2006). En los contratos dirigidos por el consumidor, las expectativas del consumidor se convierten en pruebas que el proveedor debe satisfacer; así, el proveedor solo se obliga a lo que realmente se usa y puede evolucionar sin romper a los clientes (Pact Foundation, 2026).

Además, los códigos de estado HTTP forman parte del contrato: no son un detalle del servidor, sino la forma en que el cliente distingue un éxito, un error de validación, un conflicto o una sesión vencida (MDN Web Docs, 2024). En un sistema que mueve saldos, la idempotencia y la atomicidad deben estar en el contrato y no dejarse a la interfaz. Finalmente, en un proyecto académico, el contrato demuestra que los requisitos se tradujeron en decisiones de arquitectura verificables.

## 6. Convenciones del contrato de QrPass

- Ruta base: `http://127.0.0.1:8000/api/v1` en el entorno local. En producción debe usarse HTTPS.
- Formato: JSON UTF-8. Las claves públicas están en inglés; la interfaz y los mensajes están en español.
- Autenticación: `Authorization: Bearer <access_token>`. El token dura 60 minutos.
- Roles: `PASSENGER` para pasajeros, `DRIVER` para conductores y `ADMIN` para administración. Los endpoints de conductor exigen el rol `DRIVER` y las métricas globales exigen el rol `ADMIN`.
- Dinero: enteros en pesos colombianos (COP), sin decimales.
- Fechas: ISO 8601 (`AAAA-MM-DDTHH:MM:SS`).
- Idempotencia: `idempotency_key` viaja en el cuerpo, entre 8 y 80 caracteres. La misma clave no debe producir un segundo movimiento.
- Éxito: 200 para consultas y 201 para creaciones. Errores: 400, 401, 403, 404, 409, 410, 422, 500 y 503.
- Cuerpo de error: `{"detail": "..."}`. En validación (422) se agrega `errores` con campo y mensaje.

## 7. Alcance y módulos cubiertos

Las tablas 1 a 4 cubren los cuatro módulos de la especificación de requisitos. La tabla 5 añade el módulo complementario de administración y auditoría, presente en la implementación.

- Módulo 1. Gestión de usuarios y autenticación: RF-01 y RF-02.
- Módulo 2. Procesamiento de pagos y consola a bordo: RF-03 a RF-06.
- Módulo 3. Servicios especiales y billetera virtual: RF-07 y RF-08.
- Módulo 4. Reportes, historial e información financiera: RF-09 a RF-11.
- Módulo 5. Administración y auditoría (complementario): métricas globales de recaudo.

## 8. Contrato de integración por módulo

Las tablas 1 a 5 presentan el contrato de los cuatro módulos de la especificación de requisitos y del módulo complementario de administración. Cada fila corresponde a un subrequerimiento y relaciona la pantalla, el método, el endpoint, la solicitud, la respuesta principal y los errores.

### Tabla 1. Módulo 1. Gestión de usuarios y autenticación

| Sub-RF | Pantalla y acción | Método | Endpoint | Solicitud (JSON) | Respuesta principal | Errores |
|---|---|---|---|---|---|---|
| RF-01.1 | `login.html` — Crear cuenta | POST | /auth/register | {"names":"Ana Torres","email":"ana@correo.com","password":"Clave-Segura-2026","privacy_consent":true} | 201 {"user_id":12,"username":"ana@correo.com","email":"ana@correo.com","names":"Ana Torres","roles":["PASSENGER"]} | 409 correo ya registrado; 422 datos inválidos; 503 roles no inicializados |
| RF-01.2 | `login.html` — Iniciar sesión | POST | /auth/login | {"username":"ana@correo.com","password":"Clave-Segura-2026"} | 200 {"access_token":"<token>","token_type":"bearer","expires_in":3600,"user":{...}} | 401 credenciales incorrectas o cuenta inactiva |
| RF-01.3 | `index.html` — Selección de espacio | GET | /auth/me | Sin cuerpo. Encabezado `Authorization: Bearer <token>`. | 200 {"user_id":12,"username":"...","email":"...","names":"...","roles":["PASSENGER"]} | 401 token ausente, inválido o vencido |
| RF-02.1 | `login.html` — Iniciar sesión como conductor | POST | /auth/login | {"username":"conductor@qrpass.com","password":"<contraseña>"} | 200 {"access_token":"<token>","token_type":"bearer","expires_in":3600,"user":{...,"roles":["DRIVER"]}} | 401 credenciales incorrectas o cuenta inactiva |
| RF-02.2 | `conductor.html` — Mi turno (asignación) | GET | /driver/assignment | Sin cuerpo. Requiere rol `DRIVER`. | 200 {"driver_name":"...","license_number":"...","route_id":3,"route_name":"...","vehicle_plate":"...","shift_status":"..."} | 403 sin rol DRIVER; 404 sin asignación |
| RF-02.3 | `conductor.html` — Iniciar turno | POST | /driver/shift/start?route_id=3 | Parámetro de consulta `route_id` entero mayor que cero. Sin cuerpo. | 200 {"shift_id":7,"route_id":3,"route_name":"...","vehicle_plate":"...","status":"active","starts_at":"...","cash_total":0,"qr_total":0,"card_total":0,"payment_count":0,"entries":[]} | 403 ruta no asignada; 409 sin asignación; 422 route_id inválido |

Nota. El registro crea únicamente cuentas PASSENGER; las cuentas de conductor y administración se aprovisionan con `python -m app.management create-driver` y `create-admin`. El token se envía como Bearer en todas las operaciones autenticadas.

### Tabla 2. Módulo 2. Procesamiento de pagos y consola a bordo

| Sub-RF | Pantalla y acción | Método | Endpoint | Solicitud (JSON) | Respuesta principal | Errores |
|---|---|---|---|---|---|---|
| RF-03.1 | `pasajero.html` — Escanear QR del bus | POST | /account/qr/validate | {"token":"<contenido del QR>","idempotency_key":"qr-20261109-001","destination":"Centro"} | 201 {"payment_id":21,"trip_id":15,"route_id":3,"route_name":"...","destination":"Centro","method":"wallet","movement_type":"fare_payment","amount":3300,"currency":"COP","wallet_balance":46700,"status":"completed","created_at":"..."} | 409 saldo insuficiente, QR ya usado o clave repetida; 410 QR vencido; 422 token o destino inválido |
| RF-03.2 | `conductor.html` — Registrar efectivo | POST | /driver/shift/payments | {"method":"cash","idempotency_key":"caja-20261109-001"} | 201 {"payment_id":22,"trip_id":16,"route_id":3,"route_name":"...","method":"cash","movement_type":"fare_payment","amount":3300,"currency":"COP","wallet_balance":50000,"status":"completed","created_at":"..."} | 403 sin rol DRIVER; 409 sin turno activo o clave repetida; 422 method inválido |
| RF-03.3 | `conductor.html` — Registrar tarjeta | POST | /driver/shift/payments | {"method":"card","card_type":"debit","idempotency_key":"caja-20261109-002"} | 201 {"payment_id":23,"trip_id":17,"route_id":3,"route_name":"...","method":"card","card_type":"debit","movement_type":"fare_payment","amount":3300,"currency":"COP","status":"completed","created_at":"..."} | 403 sin rol DRIVER; 409 sin turno activo o clave repetida; 422 card_type obligatorio o no permitido |
| RF-03.4 | `pasajero.html` — Pagar pasaje (efectivo o tarjeta) | POST | /account/payments | {"route_id":3,"destination":"Centro","method":"cash","idempotency_key":"pago-20261109-001"} | 201 {"payment_id":24,"trip_id":18,"route_id":3,"route_name":"...","destination":"Centro","method":"cash","movement_type":"fare_payment","amount":3300,"currency":"COP","wallet_balance":46700,"status":"completed","created_at":"..."} | 404 ruta inexistente; 409 clave repetida; 422 wallet no permitido, destino requerido o tarjeta sin tipo |
| RF-04.1 | `conductor.html` — Mostrar QR del bus | POST | /driver/shift/qr | Sin cuerpo. Requiere rol `DRIVER` y turno activo. | 201 {"qr_id":9,"token":"...","status":"active","created_at":"...","expires_at":"...","scannable":true,"image_data_uri":"data:image/svg+xml;base64,..."} | 403 sin rol DRIVER; 409 sin turno activo |
| RF-04.2 | `conductor.html` — Renovar QR | POST | /driver/shift/qr?renew=true | Parámetro `renew=true`. Sin cuerpo. | 201 Nuevo token y nueva fecha de vencimiento; el QR anterior queda revocado. | 403 sin rol DRIVER; 409 sin turno activo |
| RF-04.3 | Servidor — Validar vigencia y uso único | POST | /account/qr/validate | {"token":"...","idempotency_key":"qr-20261109-002"} | 201 Pago y viaje creados; 410 si el QR venció; 409 si ya fue usado. | 409 QR ya usado o de otro turno; 410 vencido; 422 token inválido |
| RF-05.1 | `pasajero.html` y `conductor.html` — Selector de ruta | GET | /routes | Sin cuerpo. No requiere token en la implementación actual. | 200 [{"id":1,"name":"Ruta 1"},{"id":3,"name":"Ruta 3"}] | 500 error interno |
| RF-05.2 | `pasajero.html` — Referencia de tarifa | GET | /fares/current?route_id=3&on_date=2026-11-09 | Parámetros opcionales `route_id` y `on_date`. | 200 [{"route_id":3,"route_name":"...","day_type":"weekday","destination":"Centro","amount":3300,"currency":"COP","service_date":"2026-11-09"}] | 404 ruta sin tarifa; 422 fecha o ruta inválida |
| RF-05.3 | Servidor — Aplicar tarifa al cobrar | POST | /account/payments | {"route_id":3,"destination":"Centro","method":"cash","idempotency_key":"..."} | 201 Recibo con `amount` confirmado por el servidor. | 404 ruta; 422 destino requerido o no corresponde; 409 conflicto |
| RF-06.1 | `conductor.html` — Registrar efectivo en caja | POST | /driver/shift/payments | {"method":"cash","idempotency_key":"caja-20261109-003"} | 201 {"payment_id":25,"trip_id":19,"method":"cash","amount":3300,"status":"completed",...} | 403 sin rol DRIVER; 409 sin turno activo o clave repetida; 422 method inválido |
| RF-06.2 | `conductor.html` — Panel de recaudo del turno | GET | /driver/shift | Sin cuerpo. Requiere rol `DRIVER`. | 200 {"shift_id":7,"cash_total":9900,"qr_total":3300,"card_total":3300,"payment_count":5,"entries":[...],"status":"active",...} | 403 sin rol DRIVER; 404 sin turno activo |

Nota. El pago con saldo solo se realiza escaneando el QR del bus; `method=wallet` se rechaza en el pago manual. Los pagos con tarjeta se registran para el control del turno y no pasan por un adquirente. La clave de idempotencia evita duplicar el movimiento.

### Tabla 3. Módulo 3. Servicios especiales y billetera virtual

| Sub-RF | Pantalla y acción | Método | Endpoint | Solicitud (JSON) | Respuesta principal | Errores |
|---|---|---|---|---|---|---|
| RF-07.1 | `pasajero.html` — Tarjeta de saldo | GET | /account | Sin cuerpo. Requiere sesión. | 200 {"user_id":12,"names":"Ana Torres","wallet_balance":50000,"currency":"COP"} | 401 sesión requerida |
| RF-07.2 | `pasajero.html` — Montos predefinidos | POST | /account/top-ups | {"amount":10000,"idempotency_key":"rec-20261109-001"} | 201 {"payment_id":26,"movement_type":"top_up","amount":10000,"currency":"COP","wallet_balance":60000,"status":"completed",...} | 409 clave repetida; 422 monto inválido |
| RF-07.3 | `pasajero.html` — Otro monto | POST | /account/top-ups | {"amount":25000,"idempotency_key":"rec-20261109-002"} | 201 Recibo de recarga con el saldo resultante. | 422 monto menor o igual a cero o mayor a 500000; 409 clave repetida |
| RF-07.4 | `pasajero.html` — Historial de movimientos | GET | /payments/history | Sin cuerpo. Requiere sesión. | 200 [{"payment_id":26,"movement_type":"top_up","amount":10000,"currency":"COP","balance_before":50000,"balance_after":60000,"status":"completed",...}] | 401 sesión requerida |
| RF-08.1 | `pasajero.html` — Viajes elegibles para traspaso | GET | /trips | Sin cuerpo. Requiere sesión. | 200 [{"trip_id":15,"route_id":3,"route_name":"...","payment_id":21,"method":"cash","amount":3300,"status":"completed","transferred_to":null,...}] | 401 sesión requerida |
| RF-08.2 | `pasajero.html` — Modal Transfiere tu pago | POST | /account/transfers | {"trip_id":15,"destination_route_id":4} | 201 {"transfer_id":8,"origin_trip_id":15,"origin_route":"Ruta 3","destination_route_id":4,"destination_route":"Ruta 4","additional_charge":0,"currency":"COP",...} | 404 viaje inexistente o de otro usuario; 409 ya transferido o más de 20 minutos; 422 misma ruta |
| RF-08.3 | Servidor — Regla de 20 minutos y ruta distinta | POST | /account/transfers | {"trip_id":15,"destination_route_id":4} | 201 si el viaje es propio, no tiene traspaso previo, la ruta es distinta y no han pasado más de 20 minutos. | 409 tiempo vencido o traspaso previo; 422 misma ruta |

Nota. La recarga se abona a la billetera QrPass y es idempotente; no existe pasarela bancaria ni movimiento de dinero real. El traspaso se registra con cobro adicional cero y queda asociado al viaje original.

### Tabla 4. Módulo 4. Reportes, historial e información financiera

| Sub-RF | Pantalla y acción | Método | Endpoint | Solicitud (JSON) | Respuesta principal | Errores |
|---|---|---|---|---|---|---|
| RF-09.1 | `pasajero.html` — Comprobante de pago | POST | /account/payments o /account/qr/validate | La solicitud es la del pago correspondiente. | 201 ReciboPago con `payment_id`, `trip_id`, `amount`, `status` y `created_at`. | Los errores del pago que lo originó |
| RF-09.2 | `pasajero.html` — Historial | GET | /payments/history | Sin cuerpo. Requiere sesión. | 200 Lista de movimientos con `balance_before` y `balance_after`. | 401 sesión requerida |
| RF-09.3 | `pasajero.html` — Mis viajes | GET | /trips | Sin cuerpo. Requiere sesión. | 200 Lista de viajes del usuario autenticado. | 401 sesión requerida |
| RF-09.4 | `pasajero.html` — Detalle del viaje | GET | /trips/{trip_id} | Parámetro de ruta `trip_id` entero mayor que cero. | 200 ViajeRespuesta con ruta, pago, medio, monto, estado y fecha. | 404 no encontrado o de otro usuario |
| RF-10.1 | `conductor.html` — Resumen del turno | GET | /driver/shift | Sin cuerpo. Requiere rol `DRIVER`. | 200 Resumen del turno activo con totales y estado. | 403 sin rol DRIVER; 404 sin turno activo |
| RF-10.2 | `conductor.html` — Desglose por medio | GET | /driver/shift | Sin cuerpo. Requiere rol `DRIVER`. | 200 `cash_total`, `qr_total`, `card_total` y `payment_count`. | 403 sin rol DRIVER; 404 sin turno activo |
| RF-10.3 | `conductor.html` — Bitácora de movimientos | GET | /driver/shift | Sin cuerpo. Requiere rol `DRIVER`. | 200 `entries[]` con `payment_id`, `route_name`, `method`, `amount` y `created_at`. | 403 sin rol DRIVER; 404 sin turno activo |
| RF-11.1 | `conductor.html` — Cerrar turno | POST | /driver/shift/close | {"cash_counted":45000} | 200 {"closed":true,"shift":{...,"status":"closed","ends_at":"...","cash_total":45000,"cash_counted":45000,"cash_difference":0}} | 403 sin rol DRIVER; 409 sin turno activo; 422 cash_counted negativo |
| RF-11.2 | `conductor.html` — Historial de turnos | GET | /driver/shifts/history | Sin cuerpo. Requiere rol `DRIVER`. | 200 Lista de los últimos 20 turnos cerrados del conductor. | 403 sin rol DRIVER |

Nota. El comprobante y el historial pertenecen a la cuenta del pasajero. El cierre calcula la diferencia entre el efectivo contado y el efectivo registrado.

### Tabla 5. Módulo 5. Administración y auditoría (complementario)

| Sub-RF | Pantalla y acción | Método | Endpoint | Solicitud (JSON) | Respuesta principal | Errores |
|---|---|---|---|---|---|---|
| RF-12.1 | `index.html` — Métricas globales | GET | /admin/metrics | Sin cuerpo. Requiere rol `ADMIN`. | 200 {"total_collected":...,"cash_collected":...,"qr_collected":...,"card_collected":...,"total_trips":...,"total_transfers":...,"active_shifts":...,"total_users":...,"total_routes":...} | 401 sesión requerida; 403 sin rol ADMIN |

Nota. Este módulo complementa el alcance del sistema con la consulta de métricas globales. El acceso queda restringido al rol `ADMIN`; no existe un endpoint para restablecer datos.

### Tabla 6. Catálogo de errores y acciones del cliente

| Código | Significado | Uso en QrPass | Acción del cliente |
|---|---|---|---|
| 200 | OK | Consultas exitosas: perfil, rutas, tarifas, saldo, historial, turno. | Mostrar los datos. |
| 201 | Created | Registro, pago, recarga, traspaso, QR y cierre de turno. | Mostrar el comprobante o el recurso creado. |
| 400 | Bad Request | Solicitud mal formada. | Corregir y reintentar. |
| 401 | Unauthorized | Token ausente, inválido o vencido; credenciales incorrectas; cuenta inactiva. | Volver al inicio de sesión. |
| 403 | Forbidden | Rol insuficiente o recurso de otro usuario. | Informar sin reintentar. |
| 404 | Not Found | Ruta, viaje, turno o recurso inexistente. | Informar y volver al listado. |
| 409 | Conflict | Correo duplicado, saldo insuficiente, QR ya usado, turno cerrado o clave de idempotencia repetida. | Revisar el estado antes de reintentar. |
| 410 | Gone | QR del bus vencido. | Pedir que se actualice el QR en el bus. |
| 422 | Unprocessable Entity | Validación de campos y reglas de negocio. | Mostrar el campo y el mensaje. |
| 500 | Internal Server Error | Fallo no controlado del servidor. | Reintentar o contactar soporte. |
| 503 | Service Unavailable | Base de datos no disponible o roles no inicializados. | Reintentar más tarde. |

### Tabla 7. Cobertura de subrequerimientos por módulo

| Módulo | RF | Sub-RF | Endpoints | Estado |
|---|---|---|---|---|
| 1. Usuarios y autenticación | 2 | 6 | 5 | Implementado. |
| 2. Pagos y consola a bordo | 4 | 12 | 7 | Implementado; tarjeta registrada en el turno. |
| 3. Servicios especiales y billetera | 2 | 7 | 5 | Implementado; recarga con la billetera QrPass. |
| 4. Reportes, historial y finanzas | 3 | 9 | 6 | Implementado. |
| 5. Administración y auditoría | 1 | 1 | 1 | Implementado; protegido con rol ADMIN. |
| Total | 12 | 36 | 25 | Cobertura de los cuatro módulos y un módulo complementario. |

## 9. Observaciones y brechas detectadas

1. Numeración. El documento de requisitos usa RF-01 a RF-11; la documentación interna usa RF-01 a RF-14. Este contrato adopta la numeración del documento de requisitos y añade subrequerimientos (por ejemplo, RF-03.1). Se recomienda unificar la numeración en todos los artefactos.
2. Generación del QR. El requisito RF-04 atribuye la generación al pasajero; la implementación genera el QR en la consola del bus y el pasajero lo escanea. El contrato documenta el flujo implementado y deja constancia de la diferencia para que se apruebe o se corrija.
3. Administración. `GET /admin/metrics` exige el rol `ADMIN` y no existe un endpoint para restablecer datos.
4. Pago con saldo. `POST /account/payments` rechaza `method=wallet` con 422; el pago con saldo solo se realiza escaneando el QR del bus. La regla debe permanecer explícita para evitar dos caminos para el mismo débito.
5. Idempotencia. La clave viaja en el cuerpo y no en el encabezado `Idempotency-Key`. Se documenta así porque es lo que implementa la API; cambiarla exigiría una versión nueva del contrato.
6. Registro de conductores. `POST /auth/register` crea únicamente cuentas `PASSENGER`. Las cuentas de conductor y administración se aprovisionan con `python -m app.management`; el contrato no debe prometer un auto-registro de conductores.
7. Tarifas. `GET /fares/current` devuelve una lista porque una ruta puede tener tarifas por destino y por tipo de día. La interfaz debe seleccionar la tarifa aplicable y el servidor debe confirmar el importe al cobrar.

Nota sobre el uso de IA. Para la revisión de redacción y consistencia se utilizó asistencia de inteligencia artificial. Las fuentes se verificaron y las decisiones técnicas fueron validadas por el equipo. No se cita una conversación específica porque la herramienta empleada no genera una URL pública compartible.

## 10. Referencias

- Fielding, R. T. (2000). *Architectural styles and the design of network-based software architectures* [Tesis doctoral, University of California, Irvine]. https://www.ics.uci.edu/~fielding/pubs/dissertation/top.htm
- MDN Web Docs. (2024, 24 de julio). *Códigos de estado de respuesta HTTP*. https://developer.mozilla.org/es/docs/Web/HTTP/Status
- OpenAPI Initiative. (2021). *OpenAPI Specification v3.1.0*. https://spec.openapis.org/oas/v3.1.0
- Pact Foundation. (2026). *Pact documentation*. https://docs.pact.io/
- Pressman, R. S., & Maxim, B. R. (2020). *Software engineering: A practitioner's approach* (9.ª ed.). McGraw-Hill.
- Robinson, I. (2006, 12 de junio). *Consumer-driven contracts: A service evolution pattern*. martinfowler.com. https://martinfowler.com/articles/consumerDrivenContracts.html
- Sommerville, I. (2016). *Software engineering* (10.ª ed.). Pearson.
