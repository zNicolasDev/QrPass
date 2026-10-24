# Reglas y Convenciones del Proyecto QrPass

## 1. Estructura de Análisis e Informes
Al realizar análisis, auditorías técnicas, revisiones de código o resúmenes del proyecto, organizar la presentación estrictamente en el siguiente orden de secciones:
1. **Frontend**
2. **Backend**
3. **Documentación**

## 2. Convenciones del Backend y Pruebas
- El código fuente de la API y sus modelos residen en `backend/app/`.
- Al ejecutar `pytest` desde la raíz del repositorio, utilizar siempre la opción de ruta:
  `python -m pytest -o pythonpath=backend backend/tests`
  o ejecutar los comandos directamente dentro del directorio `backend/`.
- Las pruebas de modelos y DTOs (`backend/tests/test_models_dtos.py`) pueden ejecutarse localmente sin conectividad de red.
- Las pruebas de integración con cliente HTTP (`test_api.py`) o peticiones activas de red requieren permisos de red locales en entornos restringidos.

## 3. Organización de la Documentación
- Toda la documentación técnica, especificación de requisitos (`requisitos.pdf`), matrices de trazabilidad, arquitectura y entregables UML reside centralizada en la carpeta raíz `documentacion/`.
