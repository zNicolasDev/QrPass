# 3. Planteamiento del problema

## 3.1 Contexto o situación actual

El transporte público en Ibagué enfrenta retos de recaudo: dependencia de efectivo, dificultad para conciliar turnos, riesgo de fraude y poca trazabilidad de los pagos. Los pasajeros no cuentan con un mecanismo ágil para pagar sin efectivo ni para consultar sus viajes. Los conductores deben registrar manualmente los cobros y cerrar turnos con diferencias de caja (Sommerville, 2016).

## 3.2 Necesidad o problema a resolver

Se requiere una solución que permita:

1. Registrar pagos de pasaje de forma digital y trazable.
2. Validar el pago mediante un código QR firmado asociado al turno y a la ruta del bus.
3. Evitar cobros duplicados mediante claves de idempotencia.
4. Mantener una billetera virtual por pasajero con saldo no negativo.
5. Permitir traspasos a otra ruta dentro de una ventana de 20 minutos.
6. Aplicar tarifas dinámicas por ruta y tipo de día (hábil, fin de semana, festivo).
7. Consolidar el recaudo por turno y cerrar con conciliación de efectivo.

## 3.3 Justificación del proyecto

QrPass demuestra, de extremo a extremo, el flujo de recaudo digital: desde la captura de la acción del usuario en la interfaz, la solicitud HTTP al endpoint correcto, la aplicación de validaciones y reglas de negocio en el backend, hasta la persistencia en la base de datos y la respuesta visible al usuario. La evidencia incluye casos exitosos y casos de error, lo que facilita la evaluación académica y la transferencia a un entorno productivo (Pressman & Maxim, 2020).

## Referencias

- Pressman, R. S., & Maxim, B. R. (2020). *Software engineering: A practitioner's approach* (9.ª ed.). McGraw-Hill.
- Sommerville, I. (2016). *Software engineering* (10.ª ed.). Pearson.