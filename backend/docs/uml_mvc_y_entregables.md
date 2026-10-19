# MVC y entregables UML de QrPass

Este documento muestra cómo funcionan dos procesos de QrPass: pagar un pasaje y validar un QR. Los diagramas explican el recorrido del proceso con palabras sencillas; no son diagramas de la arquitectura del backend. Debajo de cada uno se indica qué funciones de Python realizan esos pasos. Están escritos en Mermaid para poder revisarlos en GitHub o copiarlos a una herramienta UML.

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
    participant Aplicacion as Aplicación QrPass
    participant Controlador as Atención del pago
    participant Solicitud as Datos enviados por el formulario
    participant Servicio as Proceso de cobro
    participant Datos as Datos de la cuenta y del viaje
    Pasajero->>Aplicacion: Elige ruta y método de pago
    Aplicacion->>Controlador: Solicita pagar el pasaje
    Controlador->>Solicitud: Revisa los datos recibidos
    Solicitud-->>Controlador: Confirma que tienen el formato esperado
    Controlador->>Servicio: Envía los datos del pago
    Servicio->>Datos: Busca cuenta, ruta y tarifa
    Datos-->>Servicio: Devuelve la información encontrada
    Servicio->>Datos: Revisa el saldo y registra pago y viaje
    alt Saldo insuficiente
        Datos-->>Servicio: El saldo no alcanza para la tarifa
        Servicio-->>Controlador: Rechaza el pago
        Controlador-->>Aplicacion: Informa que falta saldo
        Aplicacion-->>Pasajero: Muestra el mensaje de error
    else Saldo suficiente
        Datos-->>Servicio: Confirma que guardó el pago y el viaje
        Servicio-->>Controlador: Devuelve el resultado del cobro
        Controlador-->>Aplicacion: Entrega el recibo
        Aplicacion-->>Pasajero: Muestra el recibo del viaje
    end
```

**Cómo se relaciona con Python:** FastAPI valida los datos con `CrearPagoSolicitud` y luego llama a `endpoint_pagar_viaje`; el controlador llama a `crear_pago`; finalmente, `ReciboPago` forma la respuesta. Si falta saldo, el servicio rechaza el cobro. Si alcanza, guarda el pago y el viaje juntos.

## Secuencia 2: conductor valida un QR

```mermaid
sequenceDiagram
    actor Conductor
    participant Aplicacion as Aplicación QrPass
    participant Controlador as Atención de la validación
    participant Acceso as Revisión de sesión y permiso
    participant Solicitud as Código enviado por el formulario
    participant Servicio as Proceso de revisión del QR
    participant Datos as Cuenta, turno y viaje
    Conductor->>Aplicacion: Escanea el código del pasajero
    Aplicacion->>Controlador: Envía el código para revisión
    Controlador->>Acceso: Comprueba sesión y permiso de conductor
    Acceso-->>Controlador: Autoriza la operación
    Controlador->>Solicitud: Revisa el código y la clave de reintento
    Solicitud-->>Controlador: Confirma que los datos tienen el formato esperado
    Controlador->>Servicio: Envía el código y los datos de la solicitud
    Servicio->>Datos: Busca el QR, la cuenta, el turno y la tarifa
    Datos-->>Servicio: Devuelve la información encontrada
    Servicio->>Servicio: Revisa firma, vencimiento, ruta y saldo
    alt Código vencido, alterado o no permitido
        Servicio-->>Controlador: Rechaza la validación
        Controlador-->>Aplicacion: Informa el motivo del rechazo
        Aplicacion-->>Conductor: Muestra que el viaje no fue aprobado
    else Código válido y saldo suficiente
        Servicio->>Datos: Marca el QR como usado y registra pago y viaje
        Datos-->>Servicio: Confirma que guardó la operación
        Servicio-->>Controlador: Devuelve el resultado de la validación
        Controlador-->>Aplicacion: Entrega el recibo
        Aplicacion-->>Conductor: Muestra que el viaje fue aprobado
    end
```

**Cómo se relaciona con Python:** la sesión y el rol se comprueban con `requerir_rol("DRIVER")`; `ValidacionQrConductorSolicitud` revisa los datos recibidos; `validar_y_canjear_qr` aplica las reglas; y `ReciboPago` representa la respuesta. El servicio rechaza códigos inválidos y registra el pago solo si todas las condiciones se cumplen.

## Actividad 1: pago de un viaje

```mermaid
flowchart TD
    A([Inicio]) --> B[Recibir solicitud de pago]
    B --> C{¿Los datos del pago son válidos?}
    C -- No --> X[Mostrar error de solicitud]
    C -- Sí --> D[Buscar la ruta y su tarifa]
    D --> E{¿Ruta y tarifa disponibles?}
    E -- No --> Y[Informar que no están disponibles]
    E -- Sí --> F{¿Cómo se pagará?}
    F -- Saldo --> G{¿Alcanza el saldo?}
    G -- No --> Z[Rechazar por saldo insuficiente]
    G -- Sí --> H[Descontar el valor del pasaje]
    F -- Efectivo o tarjeta --> I[No cambiar el saldo de la billetera]
    H --> J[Registrar el pago y el viaje]
    I --> J
    J --> K{¿Se pudo guardar todo?}
    K -- No --> L[Cancelar los cambios]
    K -- Sí --> M[Entregar el recibo]
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
    B --> C{¿La cuenta tiene permiso de conductor?}
    C -- No --> X[Rechazar el acceso]
    C -- Sí --> D{¿El código es auténtico y vigente?}
    D -- No --> Y[Rechazar el código]
    D -- Sí --> E{¿Tiene turno activo en esta ruta?}
    E -- No --> Y
    E -- Sí --> F{¿La cuenta del pasajero tiene saldo?}
    F -- No --> Z[Rechazar por saldo insuficiente]
    F -- Sí --> G[Marcar el código como usado]
    G --> H[Descontar el saldo y registrar el viaje]
    H --> I{¿Se guardaron todos los cambios?}
    I -- No --> J[Cancelar los cambios]
    I -- Sí --> K[Informar que el viaje fue aprobado]
    X --> L([Fin])
    Y --> L
    Z --> L
    J --> L
    K --> L
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
