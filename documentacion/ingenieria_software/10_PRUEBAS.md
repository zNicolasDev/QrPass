# 10. PRUEBAS

## 10.1. Alcance
Suite de **27 pruebas** automatizadas en `backend/tests/test_api.py` y `backend/tests/test_models_dtos.py`, ejecutadas exitosamente.

## 10.2. Tipos de Prueba
| Tipo | Cobertura |
|---|---|
| Integración API | Auth, pagos, QR, turnos, transbordos, historial |
| Modelos/DTOs | Validaciones, mapeo, relaciones |
| Idempotencia | Recargas y pagos con misma `idempotency_key` |
| Seguridad/Reglas | Token, roles, QR inválido/expirado/uso doble |
| Transaccionales | Consistencia entre entidades |

## 10.3. Resultados
```text
27 passed, 2 warnings
```

## 10.4. Casos Destacados
- Login pasajero/conductor
- Registro crea solo PASSENGER
- Pago idempotente
- QR firmado, un solo uso, ruta/turno correcto
- Saldo insuficiente no crea viaje
- Efectivo/tarjeta no modifican billetera
- Recarga idempotente
- Transbordo ventana 20 minutos
- Tarifas fin de semana/festivos
- Cierre de turno
- Historial propio
