# 6. Análisis de usuarios y casos de uso

## 6.1 Identificación de actores

**Tabla 4. Actores del sistema.**

| Actor | Descripción | Permisos |
|---|---|---|
| Pasajero | Usuario final del servicio | Consultar rutas, recargar, pagar, transferir, historial |
| Conductor | Operador del bus | Iniciar/cerrar turno, generar QR, registrar pagos |
| Sistema QrPass | Backend | Validar, persistir, responder |
| Jurado/Docente | Evaluador | Consultar documentación y demo |

## 6.2 Diagramas de casos de uso

Los casos de uso se agrupan en: autenticación, billetera, pagos, traspasos, turnos y consulta. El diagrama UML se incluye en `documentacion/arquitectura.md`.

## 6.3 Descripción de escenarios

**Tabla 5. Casos de uso principales.**

| ID | Caso de uso | Actor | Descripción resumida | Precondición | Postcondición |
|---|---|---|---|---|---|
| CU-01 | Registrarse | Pasajero | Crea cuenta | Correo no registrado | Cuenta activa |
| CU-02 | Iniciar sesión | Pasajero/Conductor | Obtiene token | Credenciales válidas | Token emitido |
| CU-03 | Consultar saldo | Pasajero | Visualiza billetera | Sesión activa | Saldo mostrado |
| CU-04 | Recargar saldo | Pasajero | Acredita monto | Sesión activa | Saldo incrementado |
| CU-05 | Pagar con QR | Pasajero | Escanea QR y debita | QR válido y saldo suficiente | Viaje creado |
| CU-06 | Pagar manual | Pasajero/Conductor | Registra pago | Ruta válida | Viaje creado |
| CU-07 | Transferirse | Pasajero | Traspaso a otra ruta | Viaje reciente (≤20 min) | Traspaso registrado |
| CU-08 | Consultar historial | Pasajero | Lista viajes/movimientos | Sesión activa | Historial mostrado |
| CU-09 | Iniciar turno | Conductor | Asocia ruta y vehículo | Rol DRIVER | Turno activo |
| CU-10 | Generar QR | Conductor | Crea QR firmado | Turno activo | QR disponible |
| CU-11 | Cerrar turno | Conductor | Concilia y finaliza | Turno activo | Turno cerrado |

### 6.3.1 Escenario detallado: CU-05 Pagar con QR

1. El conductor inicia turno y genera QR.
2. El pasajero escanea el QR desde la interfaz.
3. La API valida firma, vigencia y turno/ruta.
4. Se debita el saldo y se crea el viaje.
5. Se retorna recibo y saldo actualizado.
6. Caso de error: saldo insuficiente → 409, sin cambios.

## Referencias

- Jacobson, I., Booch, G., & Rumbaugh, J. (1999). *The unified software development process*. Addison-Wesley.
- Pressman, R. S., & Maxim, B. R. (2020). *Software engineering: A practitioner's approach* (9.ª ed.). McGraw-Hill.