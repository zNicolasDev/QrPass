# 14. CONCLUSIONES Y RECOMENDACIONES

## 14.1. Conclusiones
- Arquitectura por capas clara y mantenible
- Dominio bien modelado con trazabilidad financiera
- Reglas de negocio implementadas (idempotencia, QR firmado, turnos, transbordos)
- Suite de 27 pruebas valida flujos críticos
- Documentación técnica completa y trazable al código
- Prototipo funcional coherente con objetivo planteado

## 14.2. Recomendaciones
- Migrar a Alembic
- Implementar logging estructurado
- Añadir rate-limiting
- Gestionar secretos con .env obligatorio en prod
- Ampliar pruebas unitarias de `services.py`
- Considerar PostgreSQL fuera de demo
- Mantener documentación sincronizada con cambios
