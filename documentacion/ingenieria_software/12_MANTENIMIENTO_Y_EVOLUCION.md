# 12. MANTENIMIENTO Y EVOLUCIÓN

## 12.1. Buenas Prácticas
- Mantener sincronizada documentación con cambios en models/services/controllers/dtos
- Mantener DTOs separados de modelos ORM
- Usar `ErrorDominio` para reglas de negocio
- Controlar transacciones desde servicios
- Respetar restricciones únicas e idempotencia
- Ejecutar pruebas tras cambios críticos

## 12.2. Posibles Mejoras
| Mejora | Justificación |
|---|---|
| Migraciones con Alembic | Versionado formal de esquema |
| Logging estructurado | Trazabilidad en producción |
| Rate limiting | Protección auth/pagos |
| Refresh tokens | Rotación/revocación |
| Fortalecer firma QR | Mayor robustez |
| Integración con pasarela real | Evolución fuera de demo |
| Más pruebas unitarias por servicio | Mayor granularidad |

## 12.3. Checklist
- [ ] Imports correctos
- [ ] Models heredan de `Base`, DTOs de `EsquemaBase`
- [ ] Claves foráneas consistentes
- [ ] Transacciones atómicas
- [ ] Idempotencia verificada
- [ ] Tests pasan
