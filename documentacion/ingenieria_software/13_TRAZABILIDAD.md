# 13. TRAZABILIDAD

## 13.1. Matriz General
Ver `documentacion/trazabilidad/01_matriz_trazabilidad_cu.md` para el detalle CU <-> Endpoint <-> Servicio <-> Modelo <-> DTO.

## 13.2. Trazabilidad Requisitos - Pruebas
| RF | Relación | Estado |
|---|---|---|
| RF-01 | Login/auth | Cubierto |
| RF-02 | Registro pasajero | Cubierto |
| RF-04/RF-12 | Recarga idempotente | Cubierto |
| RF-05 | Efectivo/tarjeta | Cubierto |
| RF-06/RF-08 | Pago QR con saldo / validación QR | Cubierto |
| RF-07 | Turno conductor/QR/cierre | Cubierto |
| RF-09 | Tarifas por día/tipo | Cubierto |
| RF-10 | Historial pagos/viajes | Cubierto |
| RF-11 | Transbordos 20 min | Cubierto |
| RF-12 | Idempotencia | Cubierto |

## 13.3. Trazabilidad Código - Documentación
Basado en: `backend/app/models/*.py`, `backend/app/services.py`, `backend/app/controllers/*.py`, `backend/app/dtos/*.py`, `backend/app/database.py`, `backend/app/main.py`, `backend/tests/*.py`.
