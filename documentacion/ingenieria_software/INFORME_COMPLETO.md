# QrPass: Plataforma de recaudo digital para el transporte pÃºblico de IbaguÃ©

**Portada**

- **Nombre del proyecto:** QrPass â€” Sistema de pago y recaudo digital con cÃ³digo QR para el transporte pÃºblico de IbaguÃ©.
- **Integrantes del equipo:** Equipo de desarrollo QrPass (IngenierÃ­a de Sistemas).
- **Curso y docente:** IngenierÃ­a de Software â€” [Nombre del docente].
- **Fecha:** Noviembre de 2026.
- **Repositorio:** `C:\Users\nicol\Downloads\GitHub\QrPass` (rama `main`).

---

## Ãndice

1. [Portada](./00_PORTADA.md)
2. [Resumen ejecutivo](./01_RESUMEN_EJECUTIVO.md)
3. [Planteamiento del problema](./02_PLANTEAMIENTO_DEL_PROBLEMA.md)
4. [Objetivos](./03_OBJETIVOS.md)
5. [Requisitos del sistema](./04_REQUISITOS_DEL_SISTEMA.md)
6. [AnÃ¡lisis de usuarios y casos de uso](./05_ANALISIS_USUARIOS_CASOS_USO.md)
7. [DiseÃ±o del sistema](./06_DISENO_DEL_SISTEMA.md)
8. [PlanificaciÃ³n del proyecto](./07_PLANIFICACION_DEL_PROYECTO.md)
9. [MetodologÃ­a Ã¡gil seleccionada](./08_METODOLOGIA_AGIL.md)
10. [Desarrollo e implementaciÃ³n](./09_DESARROLLO_IMPLEMENTACION.md)
11. [Pruebas](./10_PRUEBAS.md)
12. [Conclusiones y recomendaciones](./11_CONCLUSIONES_RECOMENDACIONES.md)
13. [Referencias](./12_REFERENCIAS.md)
14. [Anexos](./ANEXOS/ANEXO_A_CODIGO_ESTRUCTURA.md)

---

## Lista de tablas

- Tabla 1. Requisitos funcionales del sistema.
- Tabla 2. Requisitos no funcionales del sistema.
- Tabla 3. Reglas de negocio.
- Tabla 4. Actores del sistema.
- Tabla 5. Casos de uso principales.
- Tabla 6. TecnologÃ­as y herramientas utilizadas.
- Tabla 7. Cronograma del proyecto.
- Tabla 8. Casos de prueba ejecutados.
- Tabla 9. ColecciÃ³n de endpoints principales.
- Tabla 10. Cuentas de demostraciÃ³n.

---

## Lista de figuras

- Figura 1. Arquitectura de componentes de QrPass.
- Figura 2. Flujo de pago mediante cÃ³digo QR del bus.
- Figura 3. Modelo entidad-relaciÃ³n del dominio.
- Figura 4. Secuencia de pago manual en efectivo o tarjeta.
- Figura 5. Secuencia de generaciÃ³n y validaciÃ³n de QR.

---

*Documento elaborado conforme a la GuÃ­a para el Proyecto de IngenierÃ­a de Software y a las normas APA (7.Âª ediciÃ³n) para las referencias.*

---

# 2. Resumen ejecutivo

## 2.1 DescripciÃ³n breve del proyecto

QrPass es un prototipo funcional de plataforma de pago y recaudo digital para el transporte pÃºblico de IbaguÃ©. El sistema permite que un pasajero consulte rutas y tarifas, gestione una billetera virtual, realice pagos mediante el escaneo del cÃ³digo QR que muestra el bus y consulte su historial de viajes. De forma paralela, el conductor inicia un turno, genera un QR temporal firmado, registra pagos manuales y cierra el turno con conciliaciÃ³n de efectivo (HernÃ¡ndez & Pressman, 2021; Sommerville, 2016).

La soluciÃ³n se compone de una interfaz web adaptable y progresiva (PWA) y de una API REST construida con FastAPI, SQLAlchemy 2 y Pydantic. Los datos se persisten en SQLite durante el desarrollo y la demostraciÃ³n. Todas las operaciones son de demostraciÃ³n: no se procesa dinero real ni se integran pasarelas bancarias.

## 2.2 Objetivo general

Desarrollar un prototipo de sistema de recaudo digital basado en cÃ³digos QR firmados que permita validar el flujo completo de pago, traspaso y conciliaciÃ³n de turnos en el transporte pÃºblico de IbaguÃ©, con trazabilidad de requisitos y evidencia de pruebas automatizadas.

## 2.3 Alcance

**Dentro del alcance (demostraciÃ³n):**

- Registro y autenticaciÃ³n de pasajeros y conductores con roles.
- Billetera virtual, recargas ficticias e idempotentes y consulta de saldo.
- Pago de pasaje mediante escaneo del QR del bus (firma HMAC, vigencia y asociaciÃ³n al turno).
- Pago manual simulado en efectivo o tarjeta.
- Traspaso Ãºnico a otra ruta dentro de 20 minutos.
- Tarifa dinÃ¡mica por ruta, dÃ­a hÃ¡bil, fin de semana y festivo colombiano.
- Historial de viajes y movimientos.
- GestiÃ³n de turnos del conductor: inicio, registro de pagos, generaciÃ³n de QR y cierre con conciliaciÃ³n.
- DocumentaciÃ³n de ingenierÃ­a de software, arquitectura, UML y trazabilidad.

**Fuera del alcance (pendiente para producciÃ³n):**

- Procesamiento de dinero real y pasarelas POS/bancarias.
- SincronizaciÃ³n offline operativa por lotes.
- Firma asimÃ©trica para validadores sin conexiÃ³n.
- Migraciones versionadas sobre base productiva.
- Pruebas de concurrencia, carga y seguridad avanzada.

## 2.4 PÃºblico objetivo

El sistema se orienta a tres actores: pasajeros (usuarios finales del servicio), conductores (operadores del bus) y personal tÃ©cnico/administrativo encargado de la operaciÃ³n y el soporte. La documentaciÃ³n y las cuentas de demostraciÃ³n permiten que jurados, docentes y nuevos desarrolladores comprendan y validen el prototipo sin conocimiento previo del dominio.

## Referencias

- HernÃ¡ndez, R. K., & Pressman, R. S. (2021). *Software engineering: A practitioner's approach* (9.Âª ed.). McGraw-Hill.
- Sommerville, I. (2016). *Software engineering* (10.Âª ed.). Pearson.

---

# 3. Planteamiento del problema

## 3.1 Contexto o situaciÃ³n actual

El transporte pÃºblico en IbaguÃ© enfrenta retos de recaudo: dependencia de efectivo, dificultad para conciliar turnos, riesgo de fraude y poca trazabilidad de los pagos. Los pasajeros no cuentan con un mecanismo Ã¡gil para pagar sin efectivo ni para consultar sus viajes. Los conductores deben registrar manualmente los cobros y cerrar turnos con diferencias de caja (Sommerville, 2016).

## 3.2 Necesidad o problema a resolver

Se requiere una soluciÃ³n que permita:

1. Registrar pagos de pasaje de forma digital y trazable.
2. Validar el pago mediante un cÃ³digo QR firmado asociado al turno y a la ruta del bus.
3. Evitar cobros duplicados mediante claves de idempotencia.
4. Mantener una billetera virtual por pasajero con saldo no negativo.
5. Permitir traspasos a otra ruta dentro de una ventana de 20 minutos.
6. Aplicar tarifas dinÃ¡micas por ruta y tipo de dÃ­a (hÃ¡bil, fin de semana, festivo).
7. Consolidar el recaudo por turno y cerrar con conciliaciÃ³n de efectivo.

## 3.3 JustificaciÃ³n del proyecto

QrPass demuestra, de extremo a extremo, el flujo de recaudo digital: desde la captura de la acciÃ³n del usuario en la interfaz, la solicitud HTTP al endpoint correcto, la aplicaciÃ³n de validaciones y reglas de negocio en el backend, hasta la persistencia en la base de datos y la respuesta visible al usuario. La evidencia incluye casos exitosos y casos de error, lo que facilita la evaluaciÃ³n acadÃ©mica y la transferencia a un entorno productivo (Pressman & Maxim, 2020).

## Referencias

- Pressman, R. S., & Maxim, B. R. (2020). *Software engineering: A practitioner's approach* (9.Âª ed.). McGraw-Hill.
- Sommerville, I. (2016). *Software engineering* (10.Âª ed.). Pearson.

---

# 4. Objetivos

## 4.1 Objetivo general

DiseÃ±ar e implementar un prototipo de plataforma de recaudo digital con cÃ³digos QR firmados para el transporte pÃºblico de IbaguÃ©, que permita validar flujos de pago, traspaso y conciliaciÃ³n de turnos con trazabilidad de requisitos y pruebas automatizadas.

## 4.2 Objetivos especÃ­ficos

1. Implementar la autenticaciÃ³n y autorizaciÃ³n por roles (pasajero y conductor) mediante tokens bearer firmados con HMAC.
2. Modelar el dominio de transporte (usuarios, roles, rutas, tarifas, turnos, pagos, viajes, QR y transbordos) en SQLAlchemy.
3. Construir una API REST con validaciones de entrada y salida mediante DTOs Pydantic.
4. Desarrollar una interfaz web adaptable (PWA) que consuma la API y muestre respuestas y errores de forma intuitiva.
5. Garantizar propiedades ACID en las transacciones de dÃ©bito, recarga y pago.
6. Aplicar tarifas dinÃ¡micas segÃºn ruta, dÃ­a hÃ¡bil, fin de semana y festivo colombiano.
7. Validar el flujo de integraciÃ³n completo (pantalla â†’ JavaScript â†’ API â†’ backend â†’ base de datos) con casos exitosos y de error.
8. Documentar la arquitectura, los casos de uso, las pruebas y la trazabilidad de requisitos bajo normas APA 7.

## Referencias

- Pressman, R. S., & Maxim, B. R. (2020). *Software engineering: A practitioner's approach* (9.Âª ed.). McGraw-Hill.

---

# 5. Requisitos del sistema

## 5.1 Requisitos funcionales

**Tabla 1. Requisitos funcionales del sistema.**

| ID | DescripciÃ³n | Endpoint principal |
|---|---|---|
| RF-01 | Registro y autenticaciÃ³n de pasajero | `POST /api/v1/auth/register`, `POST /api/v1/auth/login` |
| RF-02 | Consulta de identidad y roles | `GET /api/v1/auth/me` |
| RF-03 | Billetera y saldo | `GET /api/v1/demo/account` |
| RF-04 | Recarga ficticia e idempotente | `POST /api/v1/demo/account/top-ups` |
| RF-05 | Pago manual (efectivo/tarjeta) | `POST /api/v1/demo/account/payments` |
| RF-06 | Pago mediante QR del bus | `POST /api/v1/demo/account/qr/validate` |
| RF-07 | Traspaso a otra ruta (â‰¤ 20 min) | `POST /api/v1/demo/account/transfers` |
| RF-08 | Historial de viajes y movimientos | `GET /api/v1/trips`, `GET /api/v1/payments/history` |
| RF-09 | Tarifa vigente por ruta y dÃ­a | `GET /api/v1/fares/current` |
| RF-10 | GestiÃ³n de turno del conductor | `POST /api/v1/driver/shift/start`, `GET /api/v1/driver/shift` |
| RF-11 | GeneraciÃ³n de QR del turno | `POST /api/v1/driver/shift/qr` |
| RF-12 | Registro de pagos del conductor | `POST /api/v1/driver/shift/payments` |
| RF-13 | Cierre y conciliaciÃ³n de turno | `POST /api/v1/driver/shift/close` |
| RF-14 | Estado del servicio | `GET /api/v1/health`, `GET /api/v1/ready` |

### 5.1.1 DescripciÃ³n detallada de requisitos funcionales

- **RF-01:** El sistema debe permitir el registro de pasajeros con nombres, correo y contraseÃ±a. El correo debe ser Ãºnico y la contraseÃ±a tener al menos 12 caracteres.
- **RF-04:** La recarga debe ser idempotente mediante clave; montos entre $1 y $500.000.
- **RF-06:** El QR debe estar firmado con HMAC, vencer en 15 minutos y asociarse al turno activo.
- **RF-07:** El traspaso solo se permite una vez por viaje, entre rutas distintas y dentro de 20 minutos.
- **RF-09:** La tarifa depende de la ruta, el destino y el tipo de dÃ­a (hÃ¡bil $3.300, fin de semana/festivo $3.400).
- **RF-13:** El cierre de turno consolida efectivo, QR y tarjeta, y calcula la diferencia.

## 5.2 Requisitos no funcionales

**Tabla 2. Requisitos no funcionales del sistema.**

| ID | DescripciÃ³n | VerificaciÃ³n |
|---|---|---|
| RNF-01 | Tiempo de respuesta < 1,5 s en operaciones crÃ­ticas | Pruebas de carga (pendiente) |
| RNF-02 | Propiedades ACID en transacciones | `test_failed_payment_commit_rolls_back...` |
| RNF-03 | Cifrado de credenciales (hash) | InspecciÃ³n de cÃ³digo |
| RNF-04 | ValidaciÃ³n de entrada mediante DTOs | Pruebas de validaciÃ³n |
| RNF-05 | Disponibilidad verificable | `test_readiness_checks_database...` |
| RNF-06 | Interfaz adaptable y PWA | RevisiÃ³n manual |
| RNF-07 | Mensajes de error intuitivos | RevisiÃ³n de UX |

## 5.3 Reglas de negocio

**Tabla 3. Reglas de negocio.**

| ID | Regla | ImplementaciÃ³n |
|---|---|---|
| RN-01 | Saldo nunca negativo | `CheckConstraint` + servicio |
| RN-02 | Recargas > 0 y â‰¤ $500.000 | DTO `CrearRecargaSolicitud` |
| RN-03 | Idempotencia de pagos | Clave Ãºnica por usuario |
| RN-04 | QR vÃ¡lido 15 min y firmado | `servicios/qr.py` |
| RN-05 | Un pasajero no paga dos veces con el mismo QR | Consumo de QR |
| RN-06 | Traspaso â‰¤ 20 min y rutas distintas | `servicios/transbordos.py` |
| RN-07 | Tarifa dinÃ¡mica por dÃ­a | `servicios/rutas_tarifas.py` |
| RN-08 | Pago con saldo requiere QR | ValidaciÃ³n en servicio |
| RN-09 | Cuentas nuevas solo pasajero | `registrar_pasajero` |
| RN-10 | Toda solicitud recibe respuesta HTTP | Handlers globales |

## Referencias

- Pressman, R. S., & Maxim, B. R. (2020). *Software engineering: A practitioner's approach* (9.Âª ed.). McGraw-Hill.
- Sommerville, I. (2016). *Software engineering* (10.Âª ed.). Pearson.

---

# 6. AnÃ¡lisis de usuarios y casos de uso

## 6.1 IdentificaciÃ³n de actores

**Tabla 4. Actores del sistema.**

| Actor | DescripciÃ³n | Permisos |
|---|---|---|
| Pasajero | Usuario final del servicio | Consultar rutas, recargar, pagar, transferir, historial |
| Conductor | Operador del bus | Iniciar/cerrar turno, generar QR, registrar pagos |
| Sistema QrPass | Backend | Validar, persistir, responder |
| Jurado/Docente | Evaluador | Consultar documentaciÃ³n y demo |

## 6.2 Diagramas de casos de uso

Los casos de uso se agrupan en: autenticaciÃ³n, billetera, pagos, traspasos, turnos y consulta. El diagrama UML se incluye en `documentacion/arquitectura.md`.

## 6.3 DescripciÃ³n de escenarios

**Tabla 5. Casos de uso principales.**

| ID | Caso de uso | Actor | DescripciÃ³n resumida | PrecondiciÃ³n | PostcondiciÃ³n |
|---|---|---|---|---|---|
| CU-01 | Registrarse | Pasajero | Crea cuenta | Correo no registrado | Cuenta activa |
| CU-02 | Iniciar sesiÃ³n | Pasajero/Conductor | Obtiene token | Credenciales vÃ¡lidas | Token emitido |
| CU-03 | Consultar saldo | Pasajero | Visualiza billetera | SesiÃ³n activa | Saldo mostrado |
| CU-04 | Recargar saldo | Pasajero | Acredita monto | SesiÃ³n activa | Saldo incrementado |
| CU-05 | Pagar con QR | Pasajero | Escanea QR y debita | QR vÃ¡lido y saldo suficiente | Viaje creado |
| CU-06 | Pagar manual | Pasajero/Conductor | Registra pago | Ruta vÃ¡lida | Viaje creado |
| CU-07 | Transferirse | Pasajero | Traspaso a otra ruta | Viaje reciente (â‰¤20 min) | Traspaso registrado |
| CU-08 | Consultar historial | Pasajero | Lista viajes/movimientos | SesiÃ³n activa | Historial mostrado |
| CU-09 | Iniciar turno | Conductor | Asocia ruta y vehÃ­culo | Rol DRIVER | Turno activo |
| CU-10 | Generar QR | Conductor | Crea QR firmado | Turno activo | QR disponible |
| CU-11 | Cerrar turno | Conductor | Concilia y finaliza | Turno activo | Turno cerrado |

### 6.3.1 Escenario detallado: CU-05 Pagar con QR

1. El conductor inicia turno y genera QR.
2. El pasajero escanea el QR desde la interfaz.
3. La API valida firma, vigencia y turno/ruta.
4. Se debita el saldo y se crea el viaje.
5. Se retorna recibo y saldo actualizado.
6. Caso de error: saldo insuficiente â†’ 409, sin cambios.

## Referencias

- Jacobson, I., Booch, G., & Rumbaugh, J. (1999). *The unified software development process*. Addison-Wesley.
- Pressman, R. S., & Maxim, B. R. (2020). *Software engineering: A practitioner's approach* (9.Âª ed.). McGraw-Hill.

---

# 7. DiseÃ±o del sistema

## 7.1 Arquitectura propuesta

La arquitectura sigue un estilo cliente-servidor con API REST. La interfaz (PWA) consume la API mediante JSON sobre HTTP. El backend se organiza en capas: controladores, servicios, modelos y base de datos.

**Figura 1. Arquitectura de componentes de QrPass.**

```mermaid
flowchart LR
    FE[Interfaz web / PWA] -->|JSON sobre HTTP| API[FastAPI Â· app/core/main.py]
    API --> CTRL[Controladores Â· app/controllers/]
    CTRL --> DTO[DTOs Pydantic Â· app/dtos/]
    CTRL --> SVC[Servicios Â· app/servicios/]
    SVC --> ORM[Modelos SQLAlchemy Â· app/models/]
    ORM --> DB[(SQLite de desarrollo)]
    API --> HANDLERS[Handlers de error globales]
```

## 7.2 Diagramas UML

Se incluyen diagramas de clases, secuencia y actividades.

**Figura 3. Modelo entidad-relaciÃ³n del dominio.** (Ver `documentacion/arquitectura.md`.)

**Figura 4. Secuencia de pago manual.** (Ver `documentacion/arquitectura.md`.)

**Figura 5. Secuencia de generaciÃ³n y validaciÃ³n de QR.** (Ver `documentacion/arquitectura.md`.)

## 7.3 DiseÃ±o de interfaz de usuario

La interfaz es una PWA adaptable con vistas para pasajero y conductor. Se prioriza la claridad de mensajes de Ã©xito y error para usuarios no expertos. Los formularios validan campos en el cliente y muestran mensajes del backend.

## 7.4 Contrato de integraciÃ³n (resumen)

Cada requerimiento funcional se mapea a un endpoint, una solicitud y una respuesta. Ver Anexo E.

## Referencias

- Bass, L., Clements, P., & Kazman, R. (2021). *Software architecture in practice* (4.Âª ed.). Addison-Wesley.
- Fowler, M. (2018). *Patterns of enterprise application architecture*. Addison-Wesley.

---

# 8. PlanificaciÃ³n del proyecto

## 8.1 Cronograma

**Tabla 7. Cronograma del proyecto.**

| Fase | Actividad | Semanas | Entregable |
|---|---|---|---|
| 1 | AnÃ¡lisis de requisitos | 1-2 | Documento de requisitos |
| 2 | DiseÃ±o de arquitectura y UML | 3-4 | Diagramas y modelo |
| 3 | ImplementaciÃ³n del backend | 5-8 | API funcional |
| 4 | ImplementaciÃ³n del frontend (PWA) | 6-9 | Interfaz funcional |
| 5 | Pruebas y correcciones | 9-10 | Reporte de pruebas |
| 6 | DocumentaciÃ³n y entrega | 10-11 | Informe final |

## 8.2 AsignaciÃ³n de tareas

| Rol | Responsabilidad |
|---|---|
| Backend | API, servicios, modelos, pruebas |
| Frontend | Interfaz, PWA, integraciÃ³n |
| DocumentaciÃ³n | IngenierÃ­a de software, UML, trazabilidad |

## 8.3 Herramientas y tecnologÃ­as

**Tabla 6. TecnologÃ­as y herramientas utilizadas.**

| Componente | TecnologÃ­a | VersiÃ³n |
|---|---|---|
| Backend | Python | 3.10 |
| Framework API | FastAPI | 0.x |
| ORM | SQLAlchemy | 2.x |
| ValidaciÃ³n | Pydantic | 2.x |
| Base de datos | SQLite | 3.x |
| Frontend | HTML5/CSS3/JS | - |
| Pruebas | pytest | 8.x |
| Control de versiones | Git | - |
| Diagramas | Mermaid | - |

## Referencias

- Schwaber, K., & Sutherland, J. (2020). *The Scrum guide*. Scrum.org. https://scrumguides.org/

---

# 9. MetodologÃ­a Ã¡gil seleccionada

El equipo seleccionÃ³ **Scrum** por su adaptaciÃ³n a proyectos acadÃ©micos iterativos, con entregas incrementales y revisiÃ³n continua. Se justifica por la necesidad de validar flujos funcionales (pago, QR, turno) de forma temprana y ajustar requisitos con el docente.

## Roles

- **Product Owner:** docente/cliente.
- **Scrum Master:** lÃ­der del equipo.
- **Equipo de desarrollo:** backend, frontend, documentaciÃ³n.

## Artefactos

- **Product Backlog:** requisitos RF/RNF.
- **Sprint Backlog:** tareas por sprint.
- **Incremento:** prototipo funcional.

## Eventos

- Sprint Planning, Daily Scrum, Sprint Review, Sprint Retrospective.

## JustificaciÃ³n

Scrum permite inspeccionar y adaptar el producto en ciclos cortos, lo que facilita corregir errores de integraciÃ³n y validar el contrato de la API con el frontend.

## Referencias

- Schwaber, K., & Sutherland, J. (2020). *The Scrum guide*. Scrum.org. https://scrumguides.org/

---

# 10. Desarrollo e implementaciÃ³n

## 10.1 Lenguajes y frameworks utilizados

- **Backend:** Python 3.10, FastAPI, SQLAlchemy 2, Pydantic, Uvicorn.
- **Frontend:** HTML5, CSS3, JavaScript (PWA con Service Worker).
- **Base de datos:** SQLite.
- **Pruebas:** pytest, FastAPI TestClient.

## 10.2 Estructura del cÃ³digo

Ver Anexo A. El backend se organiza en capas: `core/`, `controllers/`, `dtos/`, `models/`, `seguridad/`, `servicios/`.

## 10.3 Evidencias del desarrollo

El repositorio se gestionÃ³ con Git. El historial incluye refactorizaciones por responsabilidad, rediseÃ±o premium del frontend, correcciones de codificaciÃ³n (UTF-8) y adiciÃ³n de endpoints `/` y `/health`.

## 10.4 Control de versiones

Se utiliza Git con commits descriptivos en espaÃ±ol. La rama `main` se mantiene sincronizada con `origin/main`.

## 10.5 Manejo de errores

Se implementaron handlers globales para validaciÃ³n (422), dominio (409/401/etc.) y errores inesperados (500), con mensajes en espaÃ±ol e indicaciÃ³n del campo.

## 10.6 Flujo de integraciÃ³n (segÃºn evidencia PNG)

El prototipo cumple el flujo exigido para la evidencia final de integraciÃ³n:

1. La interfaz captura una acciÃ³n del usuario (formularios de login, registro, pago, recarga, QR, traspaso, turno).
2. JavaScript envÃ­a la solicitud al endpoint correcto mediante `fetch` (`apiRequest` en `frontend/app.js`).
3. El backend aplica validaciones (DTOs Pydantic) y reglas de negocio (servicios).
4. La base de datos refleja la operaciÃ³n (SQLAlchemy, transacciones ACID).
5. La API devuelve una respuesta JSON y la interfaz la muestra (toasts, tablas, recibos).
6. Se explica un caso exitoso y un caso de error (pruebas CP-01 a CP-12 y documentaciÃ³n de pruebas).

**Ruta de integraciÃ³n:** probar la API â†’ crear la pantalla â†’ mostrar la respuesta â†’ manejar errores â†’ actualizar el DOM. Se utilizan cÃ³digos HTTP estÃ¡ndar (200, 201, 400, 401, 403, 404, 409, 410, 422, 500, 503) y `fetch` para todas las solicitudes.

## Referencias

- Chacon, S., & Straub, B. (2014). *Pro Git* (2.Âª ed.). Apress. https://git-scm.com/book/

---

# 11. Pruebas

## 11.1 Estrategia de pruebas

Se aplican pruebas unitarias e integradas con pytest. Las pruebas de modelos y DTOs verifican persistencia y validaciones. Las pruebas de integraciÃ³n usan FastAPI TestClient con base SQLite en memoria, validando flujos completos y casos de error.

## 11.2 Casos de prueba

**Tabla 8. Casos de prueba ejecutados.**

| ID | Caso | Resultado esperado | Estado |
|---|---|---|---|
| CP-01 | Health y rutas | 200 y 32 rutas | Aprobado |
| CP-02 | Login pasajero/conductor | 200 y roles correctos | Aprobado |
| CP-03 | Registro de pasajero | 201 y rol PASSENGER | Aprobado |
| CP-04 | Pago idempotente | Mismo payment_id | Aprobado |
| CP-05 | Rollback ante fallo | Saldo sin cambios | Aprobado |
| CP-06 | QR firmado y consumo Ãºnico | 201 y 409 en duplicado | Aprobado |
| CP-07 | Traspaso expirado | 409 | Aprobado |
| CP-08 | Top-up lÃ­mites | 422 si > $500.000 | Aprobado |
| CP-09 | Insuficiencia de saldo | 409 | Aprobado |
| CP-10 | Tarifas por dÃ­a | Montos correctos | Aprobado |
| CP-11 | ValidaciÃ³n de formularios | 422 con campo | Aprobado |
| CP-12 | Readiness sin BD | 503 | Aprobado |

## 11.3 Resultados

EjecuciÃ³n: `27 passed, 1 warning` (pytest, base SQLite en memoria). La advertencia corresponde a un campo deprecado de Pydantic (`exclude_none`), sin impacto funcional.

## 11.4 Cobertura

Las pruebas cubren flujos de autenticaciÃ³n, pagos, QR, traspasos, turnos y validaciones. Pendiente: pruebas de concurrencia y carga.

## Referencias

- Myers, G. J., Sandler, C., & Badgett, T. (2011). *The art of software testing* (3.Âª ed.). Wiley.

---

# 12. Conclusiones y recomendaciones

## 12.1 Logros alcanzados

- Se implementÃ³ un prototipo funcional de recaudo digital con QR firmado, traspasos y conciliaciÃ³n de turnos.
- Se validÃ³ el flujo de integraciÃ³n completo (pantalla â†’ JavaScript â†’ API â†’ backend â†’ base de datos) con casos exitosos y de error.
- Se documentÃ³ la arquitectura, los requisitos, las pruebas y la trazabilidad.
- Las 27 pruebas automatizadas pasan correctamente.
- Se mejorÃ³ el manejo de errores con mensajes intuitivos por campo.

## 12.2 Dificultades encontradas

- Manejo de codificaciÃ³n (UTF-8) en consola Windows y Swagger.
- RefactorizaciÃ³n de un servicio monolÃ­tico a mÃ³dulos por responsabilidad.
- AlineaciÃ³n entre el esquema formal y la implementaciÃ³n demo.

## 12.3 Posibles mejoras

- Implementar migraciones versionadas.
- AÃ±adir pruebas de concurrencia y carga.
- Integrar pasarela POS/bancaria real.
- Implementar sincronizaciÃ³n offline por lotes.
- ValidaciÃ³n de edad en registro (mÃ­nimo 5 aÃ±os).
- Mejorar mensajes de error para usuarios no expertos.

## Referencias

- Sommerville, I. (2016). *Software engineering* (10.Âª ed.). Pearson.

---

# 13. Referencias

Las referencias se presentan en formato APA (7.Âª ediciÃ³n).

- Bass, L., Clements, P., & Kazman, R. (2021). *Software architecture in practice* (4.Âª ed.). Addison-Wesley.
- Chacon, S., & Straub, B. (2014). *Pro Git* (2.Âª ed.). Apress. https://git-scm.com/book/
- FastAPI. (2024). *FastAPI documentation*. https://fastapi.tiangolo.com/
- HernÃ¡ndez, R. K., & Pressman, R. S. (2021). *Software engineering: A practitioner's approach* (9.Âª ed.). McGraw-Hill.
- Jacobson, I., Booch, G., & Rumbaugh, J. (1999). *The unified software development process*. Addison-Wesley.
- Myers, G. J., Sandler, C., & Badgett, T. (2011). *The art of software testing* (3.Âª ed.). Wiley.
- Pressman, R. S., & Maxim, B. R. (2020). *Software engineering: A practitioner's approach* (9.Âª ed.). McGraw-Hill.
- Schwaber, K., & Sutherland, J. (2020). *The Scrum guide*. Scrum.org. https://scrumguides.org/
- Sommerville, I. (2016). *Software engineering* (10.Âª ed.). Pearson.
- SQLAlchemy. (2024). *SQLAlchemy 2.0 documentation*. https://docs.sqlalchemy.org/
- Pydantic. (2024). *Pydantic documentation*. https://docs.pydantic.dev/

---


