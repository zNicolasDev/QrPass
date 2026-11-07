# 12. Conclusiones y recomendaciones

## 12.1 Logros alcanzados

- Se implementó un prototipo funcional de recaudo digital con QR firmado, traspasos y conciliación de turnos.
- Se validó el flujo de integración completo (pantalla → JavaScript → API → backend → base de datos) con casos exitosos y de error.
- Se documentó la arquitectura, los requisitos, las pruebas y la trazabilidad.
- Las 27 pruebas automatizadas pasan correctamente.
- Se mejoró el manejo de errores con mensajes intuitivos por campo.

## 12.2 Dificultades encontradas

- Manejo de codificación (UTF-8) en consola Windows y Swagger.
- Refactorización de un servicio monolítico a módulos por responsabilidad.
- Alineación entre el esquema formal y la implementación demo.

## 12.3 Posibles mejoras

- Implementar migraciones versionadas.
- Añadir pruebas de concurrencia y carga.
- Integrar pasarela POS/bancaria real.
- Implementar sincronización offline por lotes.
- Validación de edad en registro (mínimo 5 años).
- Mejorar mensajes de error para usuarios no expertos.

## Referencias

- Sommerville, I. (2016). *Software engineering* (10.ª ed.). Pearson.