# Convenciones de Desarrollo y Trabajo en Equipo - QrPass

Este documento describe las pautas técnicas, estructura de entregables y convenciones de ejecución acordadas por el equipo de desarrollo para el proyecto integrador **QrPass (SISTUR Ibagué)**.

---

## 1. Estructura de Análisis, Informes y Revisiones
Al elaborar revisiones de código, auditorías técnicas o informes de arquitectura, organizar la documentación y presentaciones estrictamente en el siguiente orden:
1. **Frontend**
2. **Backend**
3. **Documentación**

Esto garantiza coherencia metodológica y facilita la evaluación progresiva del sistema ante docentes y jurados.

---

## 2. Convenciones de Ejecución del Backend y Pruebas
* **Ubicación del código fuente:** El paquete principal de la API (`app`) y sus módulos residen en `backend/app/`.
* **Rutas de importación en pruebas:** Al ejecutar `pytest` desde la raíz del repositorio, utilizar siempre la opción de ruta:
  ```powershell
  python -m pytest -o pythonpath=backend backend/tests
  ```
  O ingresar previamente a la carpeta `backend/`:
  ```powershell
  Set-Location backend
  python -m pytest
  ```
* **Pruebas sin red:** Las pruebas de modelos y DTOs (`backend/tests/test_models_dtos.py`) operan en memoria local sin requerir conectividad externa.
* **Pruebas de cliente HTTP:** Los escenarios de integración completa (`test_api.py`) utilizan el cliente de pruebas de FastAPI con base de datos en memoria.

---

## 3. Organización de la Documentación
* Toda la documentación de requisitos (`requisitos.pdf`), arquitectura, matrices de trazabilidad y diagramas UML reside centralizada en la carpeta raíz [`documentacion/`](./).
