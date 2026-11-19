# Documentación de QrPass (SISTUR Ibagué)

Esta carpeta centraliza toda la documentación técnica, especificación de requerimientos, matrices de trazabilidad y modelos de diseño arquitectónico del proyecto QrPass.

---

## Índice Documental

### 1. Requerimientos del Sistema
* [`ingenieria_software/04_REQUISITOS_DEL_SISTEMA.md`](./ingenieria_software/04_REQUISITOS_DEL_SISTEMA.md): Lista vigente de requerimientos funcionales, no funcionales y de dominio.
* [`ingenieria_software/CONTRATO_INTEGRACION_POR_REQUERIMIENTO_FUNCIONAL.md`](./ingenieria_software/CONTRATO_INTEGRACION_POR_REQUERIMIENTO_FUNCIONAL.md): Contrato canónico por RF, con solicitud, respuesta y errores de cada endpoint.
* [`trazabilidad.md`](./trazabilidad.md): Matriz que compara cada requisito con su estado real de implementación (completo, parcial o pendiente de servicios externos).

### 2. Arquitectura y Diseño
* [`arquitectura.md`](./arquitectura.md): Arquitectura del sistema, diagramas de componentes en Mermaid, contratos REST, justificación del patrón MVC adaptado y alineación entre requisitos y código.
* [`ingenieria_software/CONTRATO_INTEGRACION_FRONTEND.md`](./ingenieria_software/CONTRATO_INTEGRACION_FRONTEND.md): Contrato de integración de los tres módulos del frontend; conserva la numeración interna anterior y complementa al contrato por requerimiento.
* [`ingenieria_software/INFORME_COMPLETO.md`](./ingenieria_software/INFORME_COMPLETO.md): Informe de Ingeniería de Software en formato Markdown, con diagramas, tablas y evidencias. Es la fuente editable del informe.

### Entregables binarios canónicos
* [`Documento_Tecnico_QrPass.pdf`](./Documento_Tecnico_QrPass.pdf): documento técnico de Programación Web; su fuente editable es `Documento_Tecnico_QrPass.docx`.
* [`Presentacion_QrPass_ProgramacionWeb.pptx`](./Presentacion_QrPass_ProgramacionWeb.pptx): presentación de la asignatura.

Los ZIP de entrega, las copias duplicadas y los archivos temporales de Office no se versionan: se regeneran desde estas fuentes cuando se necesiten.

### 3. Modelado UML y Entregables Didácticos
* [`uml_mvc_y_entregables.md`](./uml_mvc_y_entregables.md): Diagramas de secuencia y actividad en Mermaid con explicaciones paso a paso de los procesos críticos (pago con QR, pago manual y transbordos a $0 COP).

### 4. Convenciones y Buenas Prácticas
* [`convenciones.md`](./convenciones.md): Pautas de trabajo en equipo, orden de sustentaciones e informes, y reglas de ejecución de pruebas de software.

#### Programas de Apoyo Independientes (Python)
Para sustentación académica y verificación de la lógica de los diagramas, se incluyen scripts autónomos que corren en memoria sin depender de la base de datos:

| Proceso | Archivo | Comando de Ejecución |
|---|---|---|
| Secuencia 1: Pago manual | [`secuencia_pago_manual.py`](./secuencia_pago_manual.py) | `python documentacion/secuencia_pago_manual.py` |
| Secuencia 2: QR del bus | [`secuencia_qr_bus.py`](./secuencia_qr_bus.py) | `python documentacion/secuencia_qr_bus.py` |
| Actividad 1: Pago con QR | [`actividad_pago_qr.py`](./actividad_pago_qr.py) | `python documentacion/actividad_pago_qr.py` |
| Actividad 2: Transbordo | [`actividad_transbordo.py`](./actividad_transbordo.py) | `python documentacion/actividad_transbordo.py` |

---

## Guía Rápida del Patrón MVC para Sustentaciones

Para explicar de forma simple el diseño ante profesores o compañeros (siguiendo el principio **KISS**):

1. **Vista (`frontend/`):**
   * Es la pantalla que ve el usuario en el navegador o celular. No procesa datos pesados; captura los clics, muestra el saldo y envía peticiones HTTP en formato JSON.
2. **Controlador (`backend/app/controllers/`):**
   * Es la puerta de entrada de la API. Recibe la petición HTTP, revisa quién la envía (autenticación) y responde al cliente. No hace cálculos complejos directamente.
3. **DTOs (`backend/app/dtos/`):**
   * Son las "aduanas" de datos. Definen exactamente qué datos deben llegar y cuáles deben salir en el JSON (validan tipos, correos y montos con Pydantic).
4. **Servicios (`backend/app/servicios/`):**
   * Es el "cerebro" o lógica de negocio. Aplica las reglas del transporte: calcula si hoy es festivo para cobrar la tarifa de domingo o día hábil para la tarifa ordinaria, firma el código QR, verifica los 20 minutos de transbordo y suma los totales. Mantiene a los controladores limpios y simples.
5. **Modelo (`backend/app/models/`):**
   * Es la persistencia. Son las clases de SQLAlchemy que representan las tablas en la base de datos (`qrpass.db`): Usuarios, Viajes, Pagos, Rutas y Turnos.

---

## Estructura General del Proyecto

* [`frontend/`](../frontend/): Interfaz PWA con páginas diferenciadas para acceso, pasajero y conductor, más plantilla compartida de trabajo (HTML5, CSS3 y JavaScript nativo).
* [`backend/`](../backend/): API transaccional en FastAPI, modelos SQLAlchemy, contratos Pydantic y pruebas automatizadas.
* [`documentacion/`](./): Documentación técnica, académica y normativa.
