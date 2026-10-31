# 4. ANÁLISIS Y DISEÑO

## 4.1. Análisis del Dominio
El dominio se centra en: Usuario, Roles, Conductor, Vehículo, Empresa, Ruta, Tarifa, Turno, Código QR, Pago, Viaje, Transbordo, Tarjeta.

Las entidades financieras mantienen trazabilidad: `Pago` guarda `saldo_anterior`, `saldo_posterior`, `monto`, `medio`, `tipo_movimiento` e `idempotency_key`. `Viaje` vincula el cobro con ruta, tarifa y turno cuando aplica.

## 4.2. Diseño Orientado a Casos de Uso
Se identificaron casos de uso principales documentados en `documentacion/casos_de_uso/`. Cada uno mapea a endpoint, servicio y modelos ORM.

## 4.3. Patrón de Diseño
Arquitectura **MVC adaptado a FastAPI**:

- **Model (M):** `app/models/` - Entidades SQLAlchemy, relaciones, restricciones.
- **View/Representation (V):** `app/dtos/` - Esquemas Pydantic para entrada/salida.
- **Controller (C):** `app/controllers/` - Routers FastAPI, validación, inyección de dependencias.
- **Service Layer:** `app/services.py` - Lógica de negocio, reglas, transacciones.

## 4.4. Principios Aplicados
- Separación de responsabilidades (SRP)
- Inversión de dependencias vía `Depends()`
- Validaciones con Pydantic y excepciones de dominio (`ErrorDominio`)
- Idempotencia en operaciones financieras
- Transaccionalidad para mantener consistencia
- Trazabilidad con timestamps y saldos históricos
