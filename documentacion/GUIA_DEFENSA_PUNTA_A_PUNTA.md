# Cómo explicar QrPass de punta a punta

Guía para sustentar el proyecto en lenguaje sencillo. Está pensada para leerse en
voz alta: primero la idea general, luego cada capa y al final las preguntas que
suelen salir en una defensa.

---

## 1. La idea en 30 segundos

QrPass es una aplicación para pagar el pasaje de bus en Ibagué desde el celular.
El pasajero recarga saldo en una billetera interna, el conductor muestra un
código QR que cambia cada 60 segundos, y el pasajero lo escanea para pagar.
También se puede pagar en efectivo o con tarjeta, y hay transbordos sin costo.
Todo lo que se ve —rutas, tarifas, usuarios, turnos, pagos y viajes— está en una
base de datos SQLite llamada `qrpass.db`. No hay rutas ni precios escritos dentro
del código.

La frase clave: **“el código solo contiene reglas; los datos viven en la base”**.

---

## 2. Qué problema resuelve

Antes, el pasajero necesitaba efectivo exacto y el conductor llevaba un registro
en papel. Con QrPass:

- El pasajero ve su saldo, recarga y paga con el celular.
- El conductor inicia un turno, muestra un QR de un solo uso y registra lo que
  recibe en efectivo o tarjeta.
- Cada pago queda guardado con hora, ruta, valor y método.
- Si se equivoca de bus, puede pedir un transbordo a otra ruta sin pagar de nuevo
  (dentro de los 20 minutos).
- El profesor puede comprobar que no hay “datos quemados” cambiando una tarifa
  en la base y viendo cómo cambia la aplicación.

---

## 3. Alcance: qué sí hace

- Registro de pasajeros con correo, clave y consentimiento de privacidad.
- Inicio de sesión con token que vence en 1 hora.
- Recarga de billetera con límite de $500.000 por operación.
- Pago de pasaje con tarjeta débito/crédito, en efectivo (lo registra el
  conductor) y con saldo QR.
- Código QR firmado, vigente 60 segundos y de un solo uso.
- Idempotencia: si el celular repite una petición por falla de red, no se cobra
  dos veces.
- Turnos de conductor: asignación, inicio, QR, recaudo, totales, cierre con
  conteo de efectivo e historial.
- Transbordos a $0 entre rutas dentro de 20 minutos.
- Catálogo de 32 rutas y 72 tarifas guardado en la base.
- Tarifas distintas para día hábil y fin de semana/festivo; ruta 48 con tarifas
  por destino (por ejemplo, Juntas $3.800 / $3.900).
- Interfaz adaptable a móvil, instalable como PWA.
- 28 pruebas automáticas y una verificación end-to-end de 90 comprobaciones.

---

## 4. Alcance: qué NO hace (limitaciones)

Hay que decirlo con naturalidad; no es un error, es una decisión de alcance:

- **No mueve dinero real.** No hay pasarela de pago ni banco; la billetera es
  interna y los pagos con tarjeta son simulados.
- **No es un sistema de producción.** SQLite es un archivo local: sirve para la
  demo y para una sola máquina, no para miles de buses simultáneos.
- **No tiene GPS ni rastreo de buses en tiempo real.** La ruta la define el
  turno asignado al conductor.
- **No hay panel de administración web.** Las rutas y tarifas se cargan con un
  comando de gestión o se editan en la base; eso es justo lo que se muestra en
  la demo.
- **No hay verificación de correo ni recuperación de clave.**
- **El QR se renueva solo en el servidor**; el conductor necesita internet para
  generarlo. El túnel con cloudflared es opcional y en esta máquina no está
  instalado, así que el enlace público para el celular no se crea: se usa
  `http://127.0.0.1:8000`.
- **La tarifa ordinaria del catálogo maestro es global** (la misma para todas
  las rutas en `app_config`); las excepciones por destino están modeladas solo
  para la ruta 48. La tabla `fares` sí permite tarifa por ruta.
- **La cámara no se pudo usar en la prueba automatizada** (el navegador negó el
  permiso), por eso se pegó el código a mano. La opción de cámara existe en la
  interfaz.
- **Cerrar sesión no revoca el token**: este sigue vigente hasta que vence (1
  hora). Para una demo está bien; en producción se manejaría con una lista de
  revocación.

---

## 5. Arquitectura general

```
Navegador / celular  →  Frontend (HTML + CSS + JS)  →  API FastAPI  →  qrpass.db
                                                        ↑
                                        Reglas de negocio (servicios)
```

Es un **MVC adaptado**:

- **Vista:** el frontend.
- **Controlador:** recibe la petición HTTP y delega.
- **DTO:** validan lo que entra y sale (Pydantic).
- **Servicio:** la lógica de negocio.
- **Modelo:** las tablas (SQLAlchemy).

La petición nuncasalta directamente del botón a la base: siempre pasa por el
controlador y el servicio. Eso es lo que se defiende como “separación de
responsabilidades”.

---

## 6. Frontend, explicado simple

Carpeta `frontend/`. No usa React ni Angular: es HTML, CSS y JavaScript nativo,
así que no hay que compilar nada.

Archivos principales:

- `index.html` / `index.js`: decide a qué espacio llevar al usuario según su
  sesión y su rol.
- `login.html` / `login.js`: inicio de sesión y registro.
- `pasajero.html`: saldo, recarga, escanear QR, pagar, traspaso e historial.
- `conductor.html`: turno, QR, recaudo manual, cierre e historial.
- `workspace.html` + `app.js`: la plantilla compartida donde se renderizan las
  vistas. `app.js` es el archivo grande que concentra las acciones.
- `api.js`: un solo cliente HTTP. Guarda el token en `sessionStorage`, pone la
  cabecera `Authorization` y traduce los errores.
- `cache.js`: service worker de PWA. Guarda solo la “cáscara” (HTML/CSS/JS) para
  que abra sin internet; **nunca guarda respuestas de la API**, para no mostrar
  un saldo viejo.
- `jsQR.js`: librería para leer el QR con la cámara.

Detalles que suman en la defensa:

- En HTTP local, `api.js` apunta a `http://<hostname>:8000/api/v1`. Bajo HTTPS
  (túnel) usa el mismo origen, para evitar contenido mixto.
- Los montos se formatean con `Intl.NumberFormat` en pesos colombianos.
- El HTML se escapa antes de insertarlo, para evitar inyección.
- Las claves de idempotencia se generan por acción con `crypto.randomUUID()`.
- El QR del bus se consulta cada pocos segundos y se renueva solo; hay un
  contador visible de 60 s y un botón “Nuevo QR”.
- Recién se corrigió que el pago manual mostrara la tarifa base en vez de la
  tarifa de la ruta del turno: ahora usa `getFareFor(shift.routeId)`.

---

## 7. Backend, explicado simple

Carpeta `backend/`. FastAPI porque genera automáticamente la documentación
interactiva en `/docs` y valida JSON con Pydantic.

Capas:

- `app/controllers/`: `autenticacion.py`, `pasajero.py`, `conductor.py`,
  `sistema.py`. Son las “puertas”: revisan token/rol y llaman al servicio.
- `app/dtos/`: esquemas de entrada y salida. Ejemplo: `CrearRecargaSolicitud`
  exige monto positivo; `InicioSesionSolicitud` usa alias `username/password`
  para que el JSON quede en inglés y el código en español.
- `app/servicios/`: donde están las reglas. `pagos.py`, `qr.py`, `turnos.py`,
  `transbordos.py`, `rutas_tarifas.py`, `catalogo.py`, `configuracion.py`,
  `usuarios.py`.
- `app/models/`: clases SQLAlchemy. Las tablas principales son `users`, `roles`,
  `user_roles`, `drivers`, `vehicles`, `companies`, `routes`, `fares`, `shifts`,
  `payments`, `trips`, `transfers`, `qr_codes` y `app_config`.
- `app/core/`: `main.py` crea la app, configura CORS, errores y sirve el frontend;
  `database.py` crea la conexión y prepara el esquema.
- `app/seguridad/auth.py`: contraseñas con PBKDF2 y tokens JWT HS256.
- `app/management.py`: comandos `init`, `load-catalog`, `import-catalog`,
  `create-driver`, `assign-route`, `status`.

Endpoints que conviene mencionar:

- Sistema: `/health`, `/ready`, `/routes`, `/fares/current`, `/time`.
- Sesión: `/auth/register`, `/auth/login`, `/auth/me`.
- Cuenta: `/account`, `/account/top-ups`, `/account/payments`,
  `/account/qr/validate`, `/account/transfers`.
- Historial: `/trips`, `/payments/history`.
- Conductor: `/driver/assignment`, `/driver/assignments`,
  `/driver/shift/start`, `/driver/shift`, `/driver/shift/qr`,
  `/driver/shift/payments`, `/driver/shift/close`, `/driver/shifts/history`.

Errores: la API devuelve 400/401/403/404/409/410/422 según el caso. Por ejemplo,
QR vencido es 410, QR ya usado es 409, rol incorrecto es 403.

---

## 8. Base de datos y el tema “datos quemados”

La tabla `app_config` guarda tres claves JSON:

- `roles`: los roles del sistema.
- `perfiles_roles`: qué perfiles de la interfaz puede usar cada rol.
- `catalogo`: las 32 rutas y sus tarifas.

Flujo:

1. `load-catalog --archivo catalogo.json` guarda el catálogo en `app_config`.
   El archivo **no está en el repositorio**: lo entrega quien despliega.
2. `import-catalog` lee `app_config` y llena las tablas `routes` y `fares`.
   Es idempotente: se puede correr muchas veces sin duplicar nada.
3. `iniciar.bat` ejecuta `import-catalog` antes de levantar la API.
4. En los tests, el catálogo se define en memoria (`CATALOGO_PRUEBA`), así que
   las pruebas no dependen de archivos de datos.

Explicación de 30 s para la profesora:

> “`app_config` es el recetario; `routes` y `fares` son los platos ya preparados.
> El recetario está en la base, no en el código. Si cambio un plato en la base,
> la API lo sirve nuevo sin tocar la cocina.”

La BD de entrega se guarda aparte (`qrpass.db`) y no se versiona en Git porque
tiene credenciales y datos de prueba.

---

## 9. Reglas de negocio (las que sí están en código)

Estas son reglas, no datos, por eso están en Python:

- QR vigente 60 segundos; token de sesión 3600 segundos.
- Transbordo permitido hasta 20 minutos después del viaje original.
- Recarga máxima $500.000.
- Zona horaria `America/Bogota`.
- Sábado se cobra como día hábil; domingo y festivos como fin de semana.
- Un QR solo se puede usar una vez.
- Un pago con la misma clave de idempotencia devuelve el mismo resultado.

---

## 10. Recorrido completo para contar (conductor + pasajero)

1. Se ejecuta `iniciar.bat`: importa el catálogo y abre
   `http://127.0.0.1:8000`.
2. Ingreso con `conductor@qrpass.com` / `Clave-Segura-2026`. Esa cuenta tiene
   los roles DRIVER y PASSENGER, por eso puede cambiar de espacio sin cerrar
   sesión.
3. Conductor: “Iniciar turno” en la ruta 24, vehículo ABC123.
4. Aparece el QR con contador de 60 s y el botón “Nuevo QR”.
5. Se cambia a Pasajero: recarga $100.000, comprobante REC-2.
6. “Escanear QR del bus”: se pega el token del QR (o se usa la cámara) y se
   confirma. Comprobante VIA-2, $3.300, saldo $96.700.
7. “Traspaso de ruta”: se elige la ruta 48. Comprobante TRASP-1, sin costo,
   el viaje aparece como “Traspaso desde 24”.
8. Se vuelve a Conductor: el turno muestra 1 abordaje y $3.300 en “QR / saldo”.
9. “Cerrar turno” con efectivo contado $0 (porque no hubo efectivo en ese
   turno). El sistema dice que el conteo coincide y deja una nueva asignación.

Ese recorrido se probó en navegador real y también contra la API: 90/90
comprobaciones.

---

## 11. Guion de la demo de tarifa (1 minuto)

1. `python documentacion/demo_cambio_tarifa.py` → muestra $3.300.
2. Abrir `/api/v1/fares/current?route_id=17` → `"amount": 3300`.
3. `python documentacion/demo_cambio_tarifa.py --ruta 24 --valor 3500`.
4. Recargar la misma URL → `"amount": 3500`. La pantalla del conductor dice
   “+ $ 3.500” y un pago por QR cobra $3.500.
5. `python documentacion/demo_cambio_tarifa.py --revertir` → vuelve a $3.300.

Frase final: “No cambié ni una línea de código; cambié una fila en la base”.

---

## 12. Ingeniería de software

Carpeta `documentacion/`:

- `ingenieria_software/04_REQUISITOS_DEL_SISTEMA.md`: requerimientos
  funcionales, no funcionales y de dominio.
- `CONTRATO_INTEGRACION_POR_REQUERIMIENTO_FUNCIONAL.md`: para cada requerimiento,
  solicitud, respuesta y errores.
- `CONTRATO_INTEGRACION_FRONTEND.md`: cómo se conectan los módulos de la UI.
- `trazabilidad.md`: matriz requerimiento → implementación → prueba.
- `arquitectura.md`: componentes, REST y justificación del MVC adaptado.
- `uml_mvc_y_entregables.md`: diagramas de secuencia y actividad.
- Scripts `secuencia_pago_manual.py`, `secuencia_qr_bus.py`,
  `actividad_pago_qr.py`, `actividad_transbordo.py`: ejecutan la lógica de los
  diagramas en memoria, sin depender de la API.
- `GUIA_ESTUDIO_BACKEND.md`, `convenciones.md`, `FLUJO_ACCIONES.md`.
- Entregables canónicos: `Documento_Tecnico_QrPass.docx/.pdf` y
  `Presentacion_QrPass_ProgramacionWeb.pptx`. No se versionan ZIPs ni
  temporales de Office.

Pruebas: `python -m pytest -q` desde `backend/` → **28 passed**. Cubren modelos,
DTOs, servicios y API con una base en memoria.

---

## 13. Preguntas que te puedes preparar

**Generales**

1. ¿Qué hace QrPass? → Pago de pasaje con billetera y QR; catálogo en BD.
2. ¿Por qué QR y no solo una tarjeta? → Es de un solo uso y caduca en 60 s,
   así que no se puede copiar y reutilizar.
3. ¿Qué es lo más difícil del proyecto? → Mantener el pago y el viaje
   consistentes y evitar cobros dobles con idempotencia.
4. ¿Qué harías con más tiempo? → Panel de administración, PostgreSQL, notificaciones,
   impresión de QR, recuperación de clave y revocación de tokens.

**Frontend**

5. ¿Por qué JavaScript nativo? → No hay build, es fácil de explicar y corre en
   cualquier celular; además es PWA.
6. ¿Qué es una PWA? → Una web que se puede instalar y abrir aunque falte
   internet; el service worker guarda solo la interfaz, nunca datos de la API.
7. ¿Cómo sabe la UI a qué API llamar? → `api.js`: mismo origen en HTTPS, puerto
   8000 en HTTP local.
8. ¿Dónde se guarda la sesión? → En `sessionStorage`; al cerrar la pestaña se
   borra.
9. ¿Cómo evita el doble cobro el frontend? → Genera una clave de idempotencia
   por acción y la reenvía si reintenta.
10. ¿Qué pasa si el navegador no da permiso de cámara? → Hay un campo para pegar
    el código manualmente.

**Backend**

11. ¿Por qué FastAPI? → Validación con Pydantic y documentación automática en
    `/docs`.
12. ¿Qué es un DTO? → Un esquema que valida lo que entra y define lo que sale;
    evita que datos internos se filtren en el JSON.
13. ¿Qué hace un controlador? → Recibe HTTP, autentica y delega al servicio.
14. ¿Qué hace un servicio? → Aplica las reglas de negocio y habla con los
    modelos.
15. ¿Qué es MVC adaptado? → Misma separación de responsabilidades, con DTOs y
    servicios añadidos.
16. ¿Cómo se protegen los endpoints? → JWT HS256 + roles DRIVER/PASSENGER;
    401 si no hay token, 403 si el rol no sirve.
17. ¿Cómo se guardan las claves? → PBKDF2 con sal; nunca se guarda la clave en
    texto.
18. ¿Por qué hay un `/health` y un `/ready`? → Uno dice que el proceso responde
    y el otro que la base está lista.

**Datos y reglas**

19. ¿Dónde están las rutas y tarifas? → En `qrpass.db`, tablas `app_config`,
    `routes` y `fares`.
20. ¿Cómo demuestras que no hay datos quemados? → Cambio una tarifa en la base y
    la API y la UI muestran el valor nuevo sin tocar código; guion en
    `DEMO_CAMBIO_TARIFA.md`.
21. ¿Qué es `app_config`? → Un recetario con tres claves JSON: roles,
    perfiles_roles y catálogo.
22. ¿Qué pasa si corro `import-catalog` dos veces? → No duplica nada; es
    idempotente.
23. ¿Cómo se calcula el valor de un pasaje? → Según día hábil/festivo y,
    si la ruta tiene destinos, según el destino; siempre lo calcula el servidor.
24. ¿Por qué sábado cuesta como día hábil? → Regla de negocio definida en el
    servicio `comun.py`.
25. ¿Cuánto vale el transbordo? → $0, porque el pago original ya cubre la ruta
    de destino dentro de 20 minutos.
26. ¿Qué pasa si un QR vence? → La API responde 410 y hay que generar uno nuevo.
27. ¿Y si dos pasajeros usan el mismo QR? → El primero lo consume; el segundo
    recibe 409.
28. ¿Qué es la idempotencia? → Repetir la misma petición con la misma clave
    devuelve el mismo pago en vez de cobrar otra vez.
29. ¿Cómo se cierra un turno? → Se conta el efectivo; si hay diferencia, se
    registra.
30. ¿Qué tablas guardan un viaje? → `payments` guarda el dinero y `trips` el
    viaje; `transfers` guarda los transbordos.

**Pruebas y entrega**

31. ¿Cómo se ejecuta? → `iniciar.bat` desde la raíz.
32. ¿Qué pasa si no hay cloudflared? → La app abre igual en local; el túnel
    solo sirve para probar desde el celular.
33. ¿Cómo corren las pruebas? → `cd backend` y `python -m pytest -q` (28 passed).
34. ¿Se entregó la base con datos? → Sí, `qrpass.db` aparte: 1 usuario, 1
    conductor, 32 rutas, 72 tarifas y 1 turno asignado; no se versiona en Git.
35. ¿Cuántos commits hay? → 5 commits locales; el último explica el arranque y
    la demo.
36. ¿Qué verificaste personalmente? → Recorrido real de conductor y pasajero
    (recarga, pago QR, transbordo y cierre) y 90/90 comprobaciones de API.

---

## 14. Frases para salir del paso

- “Eso es una regla de negocio, no un dato: por eso está en el servicio y no en
  la base.”
- “Ese dato sí está en la base; se puede cambiar sin tocar el código.”
- “El servidor siempre recalcula el valor; el frontend solo muestra una
  referencia.”
- “La interfaz no guarda saldos en caché precisamente para no cobrar con datos
  viejos.”
- “Para producción cambiaríamos SQLite por PostgreSQL y añadiríamos un panel
  administrativo, pero la lógica de negocio se queda igual.”

---

## 15. Comandos y datos rápidos

```powershell
# Arrancar
.\iniciar.bat

# Probar
cd backend
python -m pytest -q
python -m app.management status

# Demo de tarifa
python documentacion/demo_cambio_tarifa.py
python documentacion/demo_cambio_tarifa.py --ruta 24 --valor 3500
python documentacion/demo_cambio_tarifa.py --revertir
```

- Usuario demo: `conductor@qrpass.com` / `Clave-Segura-2026`.
- Ruta asignada: 24, vehículo ABC123.
- Tarifas: hábil $3.300, festivo $3.400; ruta 48 / Juntas $3.800 y $3.900.
- API: `http://127.0.0.1:8000/docs`.
