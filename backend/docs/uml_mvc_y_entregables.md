# MVC y entregables UML de QrPass

Este documento muestra dos procesos de QrPass: pagar al abordar escaneando el QR del bus y corregir un abordaje en la ruta equivocada mediante un transbordo. Los diagramas explican el recorrido con palabras sencillas y se relacionan con funciones reales del proyecto. Están escritos en Mermaid para poder revisarlos en GitHub o copiarlos a una herramienta UML.

## Decisión de arquitectura

QrPass usa MVC adaptado a una API web:

| Parte | Responsabilidad | Ubicación |
|---|---|---|
| Modelo | Entidades, relaciones y persistencia | `app/models/` |
| Vista | Interfaz web que presenta datos y recibe acciones | `frontend/` |
| Controlador | Recibe HTTP, usa autenticación/DTOs, llama servicios y forma respuestas | `app/controllers/` |
| Reglas de negocio | Valida pagos, QR, transbordos y turnos | `app/services.py` |

FastAPI convierte los controladores en endpoints HTTP. Los DTOs (`app/dtos/`) validan el contrato JSON de entrada y salida; complementan el modelo, no son otra capa MVC. `app/controllers/__init__.py` ensambla los controladores y `app/main.py` conecta ese router con la aplicación.

La separación es por responsabilidad, no por endpoint: `sistema.py`, `autenticacion.py`, `pasajero.py` y `conductor.py`. El ejemplo de Campo Vivo confirma el uso de carpetas `Controllers`, `Dtos` y `models`; QrPass conserva sus nombres en minúscula y español, y mantiene sus servicios porque allí ya están centralizadas las reglas.

## Secuencia 1: registrar un pago en efectivo o tarjeta

```mermaid
sequenceDiagram
    actor Pasajero
    participant Aplicacion as Aplicacion QrPass
    participant Controlador as Controlador de pasajero
    participant Solicitud as Datos del pago
    participant Servicio as Proceso de registro
    participant Datos as Ruta, tarifa, pago y viaje
    Pasajero->>Aplicacion: Elige ruta y efectivo o tarjeta
    Aplicacion->>Controlador: Solicita registrar el pago
    Controlador->>Solicitud: Valida ruta y medio de pago
    Solicitud-->>Controlador: Confirma datos correctos
    Controlador->>Servicio: Envia los datos del pago
    Servicio->>Datos: Busca ruta y tarifa vigente
    Datos-->>Servicio: Devuelve la ruta y el valor
    Servicio->>Datos: Registra el pago y el viaje
    alt Ruta inexistente o tarjeta sin tipo
        Servicio-->>Controlador: Rechaza la solicitud
        Controlador-->>Aplicacion: Devuelve el motivo
        Aplicacion-->>Pasajero: Muestra el error
    else Datos validos
        Datos-->>Servicio: Confirma la operacion
        Servicio-->>Controlador: Devuelve el recibo
        Controlador-->>Aplicacion: Presenta el resultado
        Aplicacion-->>Pasajero: Muestra el viaje registrado
    end
```

**Como se relaciona con Python:** `CrearPagoSolicitud` valida ruta y medio; `endpoint_pagar_viaje` llama a `crear_pago`; el servicio consulta ruta y tarifa y registra el pago y el viaje; `ReciboPago` forma la respuesta. Para pagar con saldo, la pantalla dirige al escaneo QR del bus.

## Secuencia 2: pasajero escanea el QR del bus

```mermaid
sequenceDiagram
    participant Aplicacion as Aplicación QrPass
    participant Controlador as Controlador de pasajero
    participant DTO as Datos del QR escaneado
    participant Servicio as Reglas de abordaje
    participant Datos as QR, saldo, turno y viaje
    actor Pasajero
    actor Bus as Pantalla del bus
    Bus-->>Pasajero: Muestra QR del turno y ruta
    Pasajero->>Aplicacion: Escanea el código del bus
    Aplicacion->>Controlador: Envía token y clave de reintento
    Controlador->>DTO: Valida formato de la solicitud
    DTO-->>Controlador: Datos correctos
    Controlador->>Servicio: Solicita validar y pagar el abordaje
    Servicio->>Datos: Busca QR, turno activo, tarifa y saldo
    Datos-->>Servicio: Devuelve los registros actuales
    Servicio->>Servicio: Verifica firma, vigencia y ruta
    alt QR vencido o saldo insuficiente
        Servicio-->>Controlador: Rechaza el abordaje
        Controlador-->>Aplicacion: Devuelve el motivo del rechazo
        Aplicacion-->>Pasajero: Muestra el error
    else QR y saldo válidos
        Servicio->>Datos: Debita saldo y registra pago y viaje
        Datos-->>Servicio: Confirma la operación
        Servicio-->>Controlador: Devuelve el recibo
        Controlador-->>Aplicacion: Presenta el resultado
        Aplicacion-->>Pasajero: Muestra el abordaje pagado
    end
```

**Cómo se relaciona con Python:** el QR del turno se genera en `crear_qr_turno_conductor`; `ValidacionQrPasajeroSolicitud` revisa token y clave de reintento; `validar_qr_de_abordaje` comprueba la firma y el turno, descuenta el saldo y registra el viaje. `ReciboPago` representa la respuesta. Un QR vigente del bus puede servir a más de un pasajero.

## Actividad 1: pagar al abordar con el QR del bus

```mermaid
flowchart TD
    A([Inicio]) --> B[El bus muestra su QR de turno y ruta]
    B --> C[El pasajero escanea el codigo]
    C --> D{El codigo tiene formato correcto?}
    D -- No --> X[Informar que el codigo no es valido]
    D -- Si --> E{Firma y vigencia correctas?}
    E -- No --> Y[Rechazar el codigo]
    E -- Si --> F{Turno activo y misma ruta?}
    F -- No --> Y
    F -- Si --> G{Saldo suficiente?}
    G -- No --> Z[Rechazar por saldo insuficiente]
    G -- Si --> H[Debitar saldo]
    H --> I[Guardar pago y viaje asociado al turno]
    I --> J{Se guardaron los dos registros?}
    J -- No --> K[Cancelar la operacion]
    J -- Si --> L[Mostrar recibo y saldo actualizado]
    X --> M([Fin])
    Y --> M
    Z --> M
    K --> M
    L --> M
```

## Actividad 2: transbordo por abordar el bus equivocado

```mermaid
flowchart TD
    A([Inicio]) --> B[Pasajero selecciona el viaje pagado]
    B --> C{¿El viaje existe y le pertenece?}
    C -- No --> X[Rechazar la solicitud]
    C -- Sí --> D{¿Ya tiene un transbordo?}
    D -- Sí --> Y[Rechazar porque ya fue transferido]
    D -- No --> E{¿Está dentro del tiempo permitido?}
    E -- No --> Z[Rechazar por tiempo vencido]
    E -- Sí --> F{¿La ruta destino es diferente y activa?}
    F -- No --> W[Solicitar otra ruta]
    F -- Sí --> G[Registrar la ruta destino sin otro cobro]
    G --> H[Mostrar el viaje corregido]
    X --> I([Fin])
    Y --> I
    Z --> I
    W --> B
    H --> I
```

## Matriz de correspondencia UML y Python

| Elemento UML | Funcionalidad del proyecto | Implementación en Python | Evidencia |
|---|---|---|---|
| Clase | Representar pasajero, ruta, tarifa, pago y viaje | `Usuario`, `Ruta`, `Tarifa`, `Pago`, `Viaje` en `app/models/` | `tests/test_models_dtos.py` verifica entidades, relaciones y persistencia |
| Secuencia de pago | Registrar un pago en efectivo o tarjeta | `controllers/pasajero.py` llama `services.crear_pago`; el servicio consulta y guarda modelos | `tests/test_api.py`: pago en efectivo/tarjeta y errores de ruta/tipo de tarjeta |
| Secuencia QR | Pasajero paga escaneando el QR del bus | `controllers/conductor.py` genera el QR; `controllers/pasajero.py` llama `services.validar_qr_de_abordaje` | `tests/test_api.py`: abordaje válido, QR alterado/vencido, saldo insuficiente |
| Actividad QR | Validar turno/ruta, firma, vigencia y saldo antes del abordaje | `validar_qr_de_abordaje` aplica las reglas y registra pago/viaje dentro de una transaccion | `tests/test_api.py`: QR valido, firma alterada, vencimiento, ruta incorrecta y saldo insuficiente |
| Actividad transbordo | Corregir el abordaje si se eligio un bus equivocado | `crear_transbordo` valida propiedad, tiempo, ruta distinta y unicidad | `tests/test_api.py`: transbordo permitido y condiciones rechazadas |

## Análisis

**¿Cómo representa el código los diagramas?** Cada mensaje de la secuencia corresponde a una llamada concreta: el frontend solicita el endpoint, FastAPI valida DTO y permisos, el controlador llama una función de servicio, el servicio consulta o modifica modelos ORM y retorna el resultado que el controlador convierte a DTO de respuesta. Las decisiones de actividad corresponden a `if`, consultas condicionales y excepciones de dominio.

**¿Qué inconsistencias había entre diseño e implementación?** El primer flujo atribuía el QR al pasajero y hacía que el conductor lo escaneara. El proceso esperado es el contrario: el bus muestra el código y el pasajero lo escanea. También se aclaró que el transbordo se usa para corregir una equivocación de bus, no para cambiar de ruta por conveniencia.

**¿Qué modificaciones fueron necesarias?** El turno del conductor ahora genera un QR firmado ligado a su ruta y turno. El pasajero envía el QR para que el backend valide la operación, descuente su saldo y registre el viaje. La interfaz explica que el transbordo sirve para corregir un abordaje equivocado. La pantalla del conductor representa el dispositivo del bus; el aparato físico todavía no está conectado.

**¿Cómo ayuda UML a reducir errores?** Hace visibles el orden de llamadas, las validaciones y los resultados alternativos antes de cambiar código. La matriz permite cotejar cada paso del diagrama con un método y una prueba, lo que ayuda a detectar validaciones omitidas, responsabilidades mezcladas y respuestas que no coinciden.
