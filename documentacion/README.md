# Documentación de QrPass (SISTUR Ibagué)

Esta carpeta centraliza toda la documentación técnica, especificación de requerimientos, matrices de trazabilidad y modelos de diseño arquitectónico del proyecto QrPass.

---

## Índice Documental

### 1. Requerimientos del Sistema
* [`requisitos.pdf`](./requisitos.pdf): Documento formal de especificación de requerimientos (29 páginas). Define los requerimientos funcionales (RF-01 a RF-11), no funcionales (RNF-01 a RNF-06), de dominio (RD-01 a RD-04), matriz de partes interesadas (*stakeholders*), historias de usuario en formato Gherkin e inventario de casos de uso (CU-01 a CU-06).
* [`trazabilidad.md`](./trazabilidad.md): Matriz de trazabilidad técnica que compara detalladamente los requisitos de la especificación frente a su estado de implementación real en el prototipo (funcionalidades completas, parciales/simuladas y requerimientos para producción).

### 2. Arquitectura y Diseño
* [`arquitectura.md`](./arquitectura.md): Especificación de la arquitectura del sistema, diagramas de componentes en Mermaid, contratos de API REST, justificación técnica del patrón MVC adaptado y alineación entre requisitos y código.

### 3. Modelado UML y Entregables Didácticos
* [`uml_mvc_y_entregables.md`](./uml_mvc_y_entregables.md): Diagramas de secuencia y actividad en Mermaid con explicaciones paso a paso de los procesos críticos (pago con QR, pago manual y transbordos a $0 COP).

### 4. Convenciones y Buenas Prácticas
* [`convenciones.md`](./convenciones.md): Pautas de trabajo en equipo, orden de sustentaciones e informes, y reglas de ejecución de pruebas de software.

#### Programas de Demostración Independientes (Python)
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
4. **Servicios (`backend/app/services.py`):**
   * Es el "cerebro" o lógica de negocio. Aplica las reglas del transporte: calcula si hoy es festivo para cobrar $3.400 o día hábil para $3.300, firma el código QR, verifica los 20 minutos de transbordo y suma los totales. Mantiene a los controladores limpios y simples.
5. **Modelo (`backend/app/models/`):**
   * Es la persistencia. Son las clases de SQLAlchemy que representan las tablas en la base de datos (`qrpass.db`): Usuarios, Viajes, Pagos, Rutas y Turnos.

---

## Estructura General del Proyecto

* [`frontend/`](../frontend/): Interfaz de usuario para pasajeros y consola de conductor (HTML5, CSS3, JS nativo, PWA).
* [`backend/`](../backend/): API transaccional en FastAPI, modelos SQLAlchemy, contratos Pydantic y pruebas automatizadas.
* [`documentacion/`](./): Documentación técnica, académica y normativa.
* [`prototipo.py`](../prototipo.py): Prototipo inicial de escritorio (Tkinter), conservado como referencia histórica.
