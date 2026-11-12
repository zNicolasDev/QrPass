# 10. Desarrollo e implementación

## 10.1 Lenguajes y frameworks utilizados

- **Backend:** Python 3.10, FastAPI, SQLAlchemy 2, Pydantic, Uvicorn.
- **Frontend:** HTML5, CSS3, JavaScript (PWA con Service Worker).
- **Base de datos:** SQLite.
- **Pruebas:** pytest, FastAPI TestClient.

## 10.2 Estructura del código

Ver Anexo A. El backend se organiza en capas: `core/`, `controllers/`, `dtos/`, `models/`, `seguridad/`, `servicios/`.

## 10.3 Evidencias del desarrollo

El repositorio se gestionó con Git. El historial incluye refactorizaciones por responsabilidad, rediseño premium del frontend, correcciones de codificación (UTF-8) y adición de endpoints `/` y `/health`.

## 10.4 Control de versiones

Se utiliza Git con commits descriptivos en español. La rama `main` se mantiene sincronizada con `origin/main`.

## 10.5 Manejo de errores

Se implementaron handlers globales para validación (422), dominio (409/401/etc.) y errores inesperados (500), con mensajes en español e indicación del campo.

## 10.6 Flujo de integración (según evidencia PNG)

La plataforma cumple el flujo exigido para la evidencia final de integración:

1. La interfaz captura una acción del usuario (formularios de login, registro, pago, recarga, QR, traspaso, turno).
2. JavaScript envía la solicitud al endpoint correcto mediante `fetch` (`apiRequest` en `frontend/app.js`).
3. El backend aplica validaciones (DTOs Pydantic) y reglas de negocio (servicios).
4. La base de datos refleja la operación (SQLAlchemy, transacciones ACID).
5. La API devuelve una respuesta JSON y la interfaz la muestra (toasts, tablas, recibos).
6. Se explica un caso exitoso y un caso de error (pruebas CP-01 a CP-12 y documentación de pruebas).

**Ruta de integración:** probar la API → crear la pantalla → mostrar la respuesta → manejar errores → actualizar el DOM. Se utilizan códigos HTTP estándar (200, 201, 400, 401, 403, 404, 409, 410, 422, 500, 503) y `fetch` para todas las solicitudes.

## Referencias

- Chacon, S., & Straub, B. (2014). *Pro Git* (2.ª ed.). Apress. https://git-scm.com/book/