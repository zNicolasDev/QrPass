# 11. Pruebas

## 11.1 Estrategia de pruebas

Se aplican pruebas unitarias e integradas con pytest. Las pruebas de modelos y DTOs verifican persistencia y validaciones. Las pruebas de integración usan FastAPI TestClient con base SQLite en memoria, validando flujos completos y casos de error.

## 11.2 Casos de prueba

**Tabla 8. Casos de prueba ejecutados.**

| ID | Caso | Resultado esperado | Estado |
|---|---|---|---|
| CP-01 | Health y rutas | 200 y 32 rutas | Aprobado |
| CP-02 | Login pasajero/conductor | 200 y roles correctos | Aprobado |
| CP-03 | Registro de pasajero | 201 y rol PASSENGER | Aprobado |
| CP-04 | Pago idempotente | Mismo payment_id | Aprobado |
| CP-05 | Rollback ante fallo | Saldo sin cambios | Aprobado |
| CP-06 | QR firmado y consumo único | 201 y 409 en duplicado | Aprobado |
| CP-07 | Traspaso expirado | 409 | Aprobado |
| CP-08 | Top-up límites | 422 si > $500.000 | Aprobado |
| CP-09 | Insuficiencia de saldo | 409 | Aprobado |
| CP-10 | Tarifas por día | Montos correctos | Aprobado |
| CP-11 | Validación de formularios | 422 con campo | Aprobado |
| CP-12 | Readiness sin BD | 503 | Aprobado |

## 11.3 Resultados

Ejecución: `27 passed, 1 warning` (pytest, base SQLite en memoria). La advertencia corresponde a un campo deprecado de Pydantic (`exclude_none`), sin impacto funcional.

## 11.4 Cobertura

Las pruebas cubren flujos de autenticación, pagos, QR, traspasos, turnos y validaciones. Pendiente: pruebas de concurrencia y carga.

## Referencias

- Myers, G. J., Sandler, C., & Badgett, T. (2011). *The art of software testing* (3.ª ed.). Wiley.