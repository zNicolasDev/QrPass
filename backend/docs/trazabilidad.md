# Trazabilidad de requisitos QrPass

Estado del prototipo respecto del documento de requisitos cargado. “Implementado” describe el alcance técnico de demostración; no significa que exista una operación aprobada o desplegada para transporte real.

## Requisitos funcionales

| ID | Requisito resumido | Estado en este prototipo | Evidencia / límite |
|---|---|---|---|
| RF-01 | Registro e identificación de pasajero | Implementado en demo | `POST /auth/register` valida correo, contraseña y consentimiento, asigna solo `PASSENGER` y crea billetera aislada. Login bearer y contraseña hash. Falta verificación de correo y proceso operativo de soporte. |
| RF-02 | Acceso conductor, ruta y operación asignadas | Parcial | Cuenta de prueba con rol `DRIVER`, asignación de ejemplo y turno sujeto a ruta en servidor. No existe gestión administrativa de conductores, vehículos ni asignaciones. |
| RF-03 | Pago mediante QR, efectivo o tarjeta | Parcial / simulado | La validación autenticada por conductor (`POST /driver/qr/validate`) verifica y consume QR, debita saldo y crea el viaje; efectivo y tarjeta se registran como demostración. El flujo de tarjeta no asocia una tarjeta guardada (`Payment.card_id` queda sin uso) ni pasa por POS/adquirente. |
| RF-04 | QR dinámico con vigencia máxima de 15 minutos | Implementado en línea | QR con payload firmado HMAC, representación SVG escaneable, fecha de expiración, revocación al renovar y consumo único. No autoriza offline ni es un tiquete real. |
| RF-05 | Aplicar la tarifa vigente | Parcial | Servicio selecciona tarifa ordinaria de lunes a sábado y festiva domingo/festivo colombiano para los datos semilla. Los importes y calendario requieren aprobación/confirmación municipal y del operador. |
| RF-06 | Registrar recaudo en efectivo | Parcial | Conductor registra efectivo dentro del turno autenticado y puede conciliarlo al cierre. El sistema no verifica físicamente el efectivo recibido. |
| RF-07 | Billetera, recarga e historial unificado de pagos | Parcial / simulada | Saldo y recarga ficticia idempotente; `GET /api/v1/payments/history` lista ingresos y egresos, con saldo antes/después y viaje asociado cuando aplica. No hay pasarela, banco ni movimiento monetario real. |
| RF-08 | Traspaso gratuito en otra ruta hasta 20 minutos | Implementado en demo | Servidor limita la operación a un viaje propio, sin traspaso anterior, una ruta distinta y no más de 20 minutos. No incluye integración con reglas o validadores del operador. |
| RF-09 | Consultar historial y detalle de viaje | Parcial | `GET /api/v1/trips` lista los viajes del usuario y `GET /api/v1/trips/{trip_id}` consulta un detalle, ambos con control de propiedad. La interfaz todavía consume su ruta compatible `/demo/account/trips`; el QR firmado se puede volver a mostrar solo durante la sesión de página. No es comprobante oficial ni historial de producción. |
| RF-10 | Desglose de recaudo por turno | Implementado en turno demo | API agrega efectivo, QR y tarjetas desde pagos asociados al turno activo y expone su bitácora. Los métodos externos siguen siendo anotaciones de demostración. |
| RF-11 | Cierre consolidado del turno | Implementado en demo | Cierre persiste hora, efectivo contado y diferencia; la respuesta devuelve los totales y `/driver/shifts/history` permite consultar los últimos 20 cierres. La operación y el informe son de demostración. |

## Requisitos no funcionales

| ID | Requisito resumido | Estado | Pendiente / evidencia necesaria |
|---|---|---|---|
| RNF-01 | Operación sin conexión y sincronización | Parcial: solo shell PWA | La interfaz está cacheada; no se crean ni validan viajes offline. Diseñar firma asimétrica, gestión de claves de dispositivo, cola durable, deduplicación, resolución de conflictos, mitigación de doble gasto y pruebas de reconciliación antes de prometerlo. |
| RNF-02 | Validación menor a 1,5 segundos | No verificado | Requiere pruebas de latencia de extremo a extremo en equipos, red y despliegue objetivo; las pruebas actuales son funcionales. |
| RNF-03 | TLS 1.3 y hash seguro | Parcial | Contraseñas se almacenan con hash; la API usa bearer y QR HMAC en línea. TLS 1.3 depende del proxy/hosting; configuración, rotación y gestión de secretos de producción pendientes. |
| RNF-04 | Transacciones ACID | Parcial, con prueba de atomicidad | Débitos/recargas y los registros que dependen de ellos se confirman en una transacción SQLAlchemy. `test_failed_payment_commit_rolls_back_balance_payment_and_trip` y `test_failed_qr_redemption_commit_restores_qr_balance_payment_and_trip` inyectan fallo pre-commit; verifican que no queda débito ni estado parcial de QR/pago/viaje. No hay prueba de aislamiento/carga concurrente sobre un motor productivo elegido. |
| RNF-05 | Compatibilidad Android 8 o superior | Parcial | Diseño adaptable y PWA; no hay matriz de dispositivos/navegadores certificados ni prueba física de Android 8. La cámara requiere navegador compatible, permiso y contexto seguro. |
| RNF-06 | Escalar 200% sin exceder 2 segundos | No verificado | Hace falta definir carga base, modelo de concurrencia, infraestructura objetivo y ejecutar benchmark con umbrales y monitoreo. |

## Requisitos de dominio y regulación

| ID | Requisito resumido | Estado | Pendiente / evidencia necesaria |
|---|---|---|---|
| RD-01 | Tarifa municipal | Parcial | La lógica de día ordinario/festivo está implementada; los importes son semilla de demostración, no tarifas autorizadas. Confirmar acto administrativo, excepciones y calendario con la autoridad. |
| RD-02 | Ley 1581/2012 y Decreto 1377/2013 | Parcial | Se solicita y registra consentimiento para el demo. Falta política aprobada, finalidades/retención, derechos del titular, controles organizacionales, evaluación jurídica y procedimientos de incidentes. |
| RD-03 | Traspaso ≤20 minutos y ruta diferente | Implementado en demo | Límite temporal, ruta distinta y uso único se validan del lado servidor. Confirmar con operador la definición exacta del inicio del cómputo y excepciones del servicio. |
| RD-04 | Regulación sectorial aplicable | Pendiente de validación | No se declara cumplimiento legal. Requiere revisión por responsables jurídicos y operador de transporte frente a la regulación aplicable al sistema, recaudo, tiquetes y operación. |

## Dependencias y decisiones necesarias

- **Pagos:** seleccionar pasarela/adquirente, proceso de autorización y conciliación, manejo de devoluciones, errores, fraude y ambiente de certificación. No solicitar ni almacenar PAN/CVV en este prototipo.
- **POS y operación:** elegir terminal, integración, identificación de vehículo/dispositivo y protocolos de arqueo. El ingreso manual no demuestra recaudo físico.
- **Sin conexión:** decidir modelo de riesgo y resolución de doble gasto entre buses desconectados. HMAC se mantiene solo para validación en línea; no distribuir la clave del servidor.
- **Despliegue:** elegir proveedor/base productiva, migraciones versionadas, TLS 1.3, secretos, copias de seguridad, monitoreo y objetivos de disponibilidad/latencia.
- **Contrato de API:** la especificación nombra algunos recursos en español y propone rutas distintas a las rutas demo actuales. Se agregaron recursos canónicos en inglés para historial unificado e historial/detalle de viajes, manteniendo compatibilidad. La homologación completa de rutas, inicio operativo de conductores y administración requiere decidir si se versiona el contrato antes de cambiar clientes.
- **Base de datos:** SQLite activa claves foráneas y el modelo declara restricciones; la inicialización todavía depende de `create_all` más ALTERs de compatibilidad, no de migraciones versionadas. Pruebas de integridad y rollback no reemplazan pruebas concurrentes ni estrategia de respaldo/restauración.
- **Comunicaciones:** `/health` indica vida del proceso y `/ready` verifica conexión a la base. El sistema no tiene mensajería asíncrona ni protocolo de sincronización offline activo; no se reportan como implementados.
- **Tarifa y regulación:** obtener datos oficiales y aprobación de autoridad/operador, y revisar privacidad/transporte con asesoría competente.
- **Trazabilidad del documento:** la matriz de casos de uso y otras tablas del PDF no siempre asignan los mismos IDs que la sección normativa. Esta tabla toma como referencia los enunciados RF-01–RF-11, RNF-01–RNF-06 y RD-01–RD-04 de sus secciones; confirmar y corregir esa numeración con el equipo antes de usarla como matriz contractual.

## Verificación reproducible

- Backend: `python -m pytest` desde `backend`.
- Frontend: `node --check frontend/app.js` desde la raíz del proyecto.
- Pruebas de API cubren roles y aislamiento de cuenta, pagos/recargas idempotentes, atomicidad de pago y validación QR bajo fallo inyectado, readiness de base de datos, reglas de tarifas y traspasos, firma/expiración/uso del QR y cierre/historial de turno. No cubren carrera concurrente ni rendimiento.
