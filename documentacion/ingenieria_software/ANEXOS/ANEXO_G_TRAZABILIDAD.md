# Anexo G. Matriz de trazabilidad (resumen)

| Requisito | Diseño | Implementación | Prueba |
|---|---|---|---|
| RF-01 | DTOs autenticación | `servicios/usuarios.py` | `test_passenger_registration...` |
| RF-05 | DTO pago | `servicios/pagos.py` | `test_cash_and_card_payments...` |
| RF-06 | QR firmado | `servicios/qr.py` | `test_bus_qr_is_signed...` |
| RF-07 | Transferencia | `servicios/transbordos.py` | `test_top_up_limits_and_transfer_rules` |
| RF-09 | Tarifa por día | `servicios/rutas_tarifas.py` | `test_saturday_sunday...` |
| RF-10/11/12/13 | Turnos | `servicios/turnos.py` | `test_driver_records_cash...` |
| RNF-02 | Transacciones | `pagos.py` | `test_failed_payment_commit...` |
| RNF-05 | Readiness | `sistema.py` | `test_readiness_checks...` |