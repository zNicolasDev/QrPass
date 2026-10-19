# MVC y entregables UML de QrPass

Este documento conecta los procesos que ya existen en QrPass con sus controladores, servicios y modelos. Los diagramas están escritos en Mermaid para poder revisarlos en GitHub o copiarlos a una herramienta UML.

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

## Secuencia 1: pagar un viaje con saldo

```mermaid
sequenceDiagram
    actor Pasajero
    participant Vista as Frontend
    participant Controlador as pasajero.py
    participant DTO as CrearPagoSolicitud
    participant Servicio as services.crear_pago
    participant Modelo as Usuario, Ruta, Tarifa, Pago, Viaje
    participant BD as SQLite
    Pasajero->>Vista: Elige ruta y saldo
    Vista->>Controlador: POST /api/v1/demo/account/payments
    Controlador->>DTO: Validar JSON
    DTO-->>Controlador: Solicitud validada
    Controlador->>Servicio: crear_pago(session, usuario, solicitud)
    Servicio->>Modelo: Consultar ruta, tarifa y saldo
    Modelo->>BD: SELECT ruta, tarifa y usuario
    BD-->>Servicio: Datos encontrados
    Servicio->>Modelo: Descontar saldo y crear Pago + Viaje
    Modelo->>BD: UPDATE condicional e INSERT transaccional
    alt Saldo insuficiente
        BD-->>Servicio: No se actualizó el saldo
        Servicio-->>Controlador: ErrorDominio 409
        Controlador-->>Vista: HTTP 409, saldo insuficiente
        Vista-->>Pasajero: Mostrar error
    else Saldo suficiente
        BD-->>Servicio: Transacción confirmada
        Servicio-->>Controlador: Pago, viaje y saldo restante
        Controlador-->>Vista: ReciboPago, HTTP 201
        Vista-->>Pasajero: Mostrar recibo
    end
```

**Orden ejecutable:** `endpoint_pagar_viaje` → DTO `CrearPagoSolicitud` → `crear_pago` → consultas/actualizaciones ORM → `ReciboPago`. La ruta comprueba saldo de nuevo en la actualización condicional para no gastar dos veces el mismo saldo.

## Secuencia 2: conductor valida un QR

```mermaid
sequenceDiagram
    actor Conductor
    participant Vista as Frontend
    participant Controlador as conductor.py
    participant Auth as UsuarioAutenticado + rol DRIVER
    participant DTO as ValidacionQrConductorSolicitud
    participant Servicio as services.validar_y_canjear_qr
    participant Modelo as Turno, CodigoQr, Usuario, Pago, Viaje
    participant BD as SQLite
    Conductor->>Vista: Escanea el QR
    Vista->>Controlador: POST /api/v1/driver/qr/validate
    Controlador->>Auth: Verificar sesión y rol
    Auth-->>Controlador: Conductor autorizado
    Controlador->>DTO: Validar token e idempotencia
    DTO-->>Controlador: Solicitud válida
    Controlador->>Servicio: validar_y_canjear_qr(session, conductor, token, secreto, clave)
    Servicio->>Modelo: Verificar turno, firma, vencimiento y ruta
    Modelo->>BD: Consultar turno, QR, ruta y tarifa
    BD-->>Servicio: Datos del viaje
    alt QR vencido, alterado o de otra ruta
        Servicio-->>Controlador: Error de dominio
        Controlador-->>Vista: HTTP 4xx/409 con detalle
        Vista-->>Conductor: Mostrar rechazo
    else QR válido
        Servicio->>Modelo: Consumir QR, debitar y registrar Pago + Viaje
        Modelo->>BD: Actualización e inserciones
        BD-->>Servicio: Transacción confirmada
        Servicio-->>Controlador: Pago, viaje y saldo
        Controlador-->>Vista: ReciboPago, HTTP 201
        Vista-->>Conductor: Mostrar validación aprobada
    end
```

**Orden ejecutable:** dependencia de rol → `endpoint_validar_qr_pasajero` → DTO → `validar_y_canjear_qr` → lectura y validación ORM → consumo y escritura → `ReciboPago`. La misma clave de idempotencia permite responder a un reintento sin cobrar dos veces.

## Actividad 1: pago de un viaje

```mermaid
flowchart TD
    A([Inicio]) --> B[Recibir solicitud de pago]
    B --> C{DTO válido?}
    C -- No --> X[Responder 422]
    C -- Sí --> D[Buscar ruta activa y tarifa vigente]
    D --> E{Ruta y tarifa existen?}
    E -- No --> Y[Responder 404]
    E -- Sí --> F{Medio de pago}
    F -- Billetera --> G{Saldo suficiente?}
    G -- No --> Z[Rollback y responder 409]
    G -- Sí --> H[Descontar saldo condicionalmente]
    F -- Efectivo/tarjeta --> I[Conservar saldo]
    H --> J[Crear pago y viaje]
    I --> J
    J --> K{Commit correcto?}
    K -- No --> L[Rollback y propagar error]
    K -- Sí --> M[Responder recibo 201]
    X --> N([Fin])
    Y --> N
    Z --> N
    L --> N
    M --> N
```

## Actividad 2: validar QR de viaje

```mermaid
flowchart TD
    A([Inicio]) --> B[Conductor envía token]
    B --> C{Sesión con rol DRIVER?}
    C -- No --> X[Responder 401 o 403]
    C -- Sí --> D{Token bien formado y firma válida?}
    D -- No --> Y[Rechazar QR]
    D -- Sí --> E{QR registrado, activo y vigente?}
    E -- No --> Y
    E -- Sí --> F{Turno activo y ruta coincidente?}
    F -- No --> Y
    F -- Sí --> G{Saldo cubre tarifa?}
    G -- No --> Z[Rechazar por saldo insuficiente]
    G -- Sí --> H[Consumir QR y debitar saldo]
    H --> I[Crear pago y viaje asociado al turno]
    I --> J{Commit correcto?}
    J -- No --> K[Rollback: QR y saldo quedan sin cambios]
    J -- Sí --> L[Responder recibo 201]
    X --> M([Fin])
    Y --> M
    Z --> M
    K --> M
    L --> M
```

## Matriz de correspondencia UML y Python

| Elemento UML | Funcionalidad del proyecto | Implementación en Python | Evidencia |
|---|---|---|---|
| Clase | Representar pasajero, ruta, tarifa, pago y viaje | `Usuario`, `Ruta`, `Tarifa`, `Pago`, `Viaje` en `app/models/` | `tests/test_models_dtos.py` verifica entidades, relaciones y persistencia |
| Secuencia de pago | Cobrar un viaje con billetera, efectivo o tarjeta | `controllers/pasajero.py` llama `services.crear_pago`; el servicio consulta y guarda modelos | `tests/test_api.py`: pago de billetera, efectivo/tarjeta, saldo insuficiente y rollback |
| Secuencia QR | Validar QR del pasajero desde el turno del conductor | `controllers/conductor.py` llama `services.validar_y_canjear_qr` | `tests/test_api.py`: QR válido, firma alterada, vencimiento, ruta incorrecta y rollback |
| Actividad de pago | Validar solicitud, ruta, tarifa, saldo y persistencia | Condiciones en `crear_pago`; DTO limita combinaciones de medio y tipo de tarjeta | Pruebas de medio inválido y saldo insuficiente |
| Actividad QR | Autorizar solo QR válido durante turno/ruta apropiados | Validaciones de firma, estado, vencimiento, turno y saldo en `validar_y_canjear_qr` | Pruebas de firma alterada, QR vencido, otra ruta y canje exitoso |

## Análisis

**¿Cómo representa el código los diagramas?** Cada mensaje de la secuencia corresponde a una llamada concreta: el frontend solicita el endpoint, FastAPI valida DTO y permisos, el controlador llama una función de servicio, el servicio consulta o modifica modelos ORM y retorna el resultado que el controlador convierte a DTO de respuesta. Las decisiones de actividad corresponden a `if`, consultas condicionales y excepciones de dominio.

**¿Qué inconsistencias había entre diseño e implementación?** Las rutas actuaban como controladores, pero el nombre `routes.py` y su concentración ocultaban esa responsabilidad. También conviven las rutas del usuario (`/demo/account/payments`) y las del conductor (`/driver/qr/validate`): son dos entradas distintas al cobro y una debe recibir el QR generado por la otra.

**¿Qué modificaciones fueron necesarias?** Se agruparon los endpoints existentes en cuatro módulos de controladores, se actualizó `main.py` para cargar su router y se eliminó el archivo `routes.py`. Los modelos, DTOs y servicios mantienen sus responsabilidades actuales. No se duplicaron reglas ni se agregaron clases vacías solo para cumplir nombres de arquitectura.

**¿Cómo ayuda UML a reducir errores?** Hace visibles el orden de llamadas, las validaciones y los resultados alternativos antes de cambiar código. La matriz permite cotejar cada paso del diagrama con un método y una prueba, lo que ayuda a detectar validaciones omitidas, responsabilidades mezcladas y respuestas que no coinciden.
