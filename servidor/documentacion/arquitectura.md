# Arquitectura inicial QrPass

## Diagrama de componentes

```mermaid
flowchart LR
    FE[Interfaz web / PWA] -->|JSON sobre HTTPS| API[FastAPI · aplicacion/inicio.py]
    API --> CTRL[Rutas · aplicacion/rutas.py]
    CTRL --> DTO[Esquemas Pydantic · aplicacion/esquemas.py]
    CTRL --> SVC[Servicios · aplicacion/servicios.py]
    SVC --> ORM[Modelos SQLAlchemy · aplicacion/modelos.py]
    ORM --> DB[(SQLite de desarrollo<br/>PostgreSQL candidato)]
    DB --> SEED[Datos iniciales · aplicacion/base_datos.py]
    TEST[pytest + TestClient] --> API
```

## Diagrama de clases / entidades

```mermaid
classDiagram
    class User {
        +int id
        +string names
        +string username
        +string email
        +string document_number
        +int wallet_balance
        +string status
        +datetime privacy_consent_at
    }
    class Role {
        +int id
        +string code
        +string name
    }
    class UserRole {
        +int id
        +int user_id
        +int role_id
    }
    class Driver {
        +int user_id
        +string license_number
    }
    class TransportCompany {
        +int id
        +string name
    }
    class Vehicle {
        +int id
        +int company_id
        +string plate
    }
    class BoardingDevice {
        +int id
        +int vehicle_id
        +string serial
    }
    class OfflineSync {
        +int id
        +int device_id
        +datetime synced_at
    }
    class Route {
        +int id
        +string name
        +bool active
    }
    class Fare {
        +int id
        +int route_id
        +string day_type
        +int amount
        +bool active
    }
    class Shift {
        +int id
        +int driver_id
        +int vehicle_id
        +int route_id
        +datetime starts_at
        +datetime ends_at
        +string status
        +int cash_counted
        +int cash_difference
    }
    class Card {
        +int id
        +int user_id
        +string bank_name
        +string card_type
        +string status
    }
    class QrCode {
        +int id
        +int user_id
        +string token
        +string status
        +datetime expires_at
    }
    class Payment {
        +int id
        +int user_id
        +int card_id
        +int qr_code_id
        +string method
        +string movement_type
        +int amount
        +int balance_before
        +int balance_after
        +string idempotency_key
        +string status
        +datetime created_at
    }
    class Trip {
        +int id
        +int payment_id
        +int shift_id
        +int fare_id
        +int route_id
        +datetime created_at
    }
    class Transfer {
        +int id
        +int origin_trip_id
        +int destination_route_id
        +datetime created_at
    }

    User "1" --> "0..*" Payment : realiza
    User "1" --> "0..*" QrCode : solicita
    User "1" --> "0..*" Card : registra
    User "1" --> "0..*" UserRole : tiene
    Role "1" --> "0..*" UserRole : asigna
    User "1" --> "0..1" Driver : puede ser
    TransportCompany "1" --> "0..*" Vehicle : opera
    Vehicle "1" --> "0..*" BoardingDevice : equipa
    BoardingDevice "1" --> "0..*" OfflineSync : sincroniza
    Driver "1" --> "0..*" Shift : trabaja
    Vehicle "1" --> "0..*" Shift : atiende
    Route "1" --> "0..*" Shift : asigna
    Route "1" --> "0..*" Fare : define
    Payment "1" --> "0..1" Trip : origina
    Shift "0..1" --> "0..*" Trip : registra
    Fare "1" --> "0..*" Trip : aplica
    Route "1" --> "0..*" Trip : aborda
    Trip "1" --> "0..1" Transfer : origina
    Route "1" --> "0..*" Transfer : destino
```

## Secuencia de pago con saldo

```mermaid
sequenceDiagram
    actor Pasajero
    participant Frontend
    participant Controller as Ruta FastAPI
    participant DTO as Esquema PaymentCreate
    participant Service as Servicio de pagos
    participant DB as SQLAlchemy / SQLite
    Pasajero->>Frontend: Selecciona ruta y saldo QR
    Frontend->>Controller: POST /api/v1/demo/account/payments
    Controller->>DTO: Valida route_id y method
    DTO-->>Controller: Solicitud validada
    Controller->>Service: create_payment(request)
    Service->>DB: Lee ruta, tarifa y saldo del usuario autenticado
    Service->>DB: Descuenta saldo condicionalmente
    alt saldo insuficiente
        DB-->>Service: 0 filas actualizadas
        Service-->>Controller: Error de dominio 409
        Controller-->>Frontend: Saldo insuficiente
    else saldo disponible
        Service->>DB: Inserta pago y viaje con clave de idempotencia
        DB-->>Service: Operación confirmada (demo)
        Service-->>Controller: Pago, viaje y saldo
        Controller-->>Frontend: Respuesta PaymentReceipt · HTTP 201
    end
```

## Contrato de ejemplo

```http
POST /api/v1/demo/account/payments
Content-Type: application/json

{"route_id": 1, "method": "wallet", "idempotency_key": "pago-intento-0001"}
```

`method` acepta `wallet`, `cash` o `card`; si es `card`, debe incluir `card_type` (`debit` o `credit`). Las respuestas incluyen `mode: "demo"` y el estado `completed_demo` para no confundir la simulación con una autorización financiera real.

## Secuencia QR y turno conductor

```mermaid
sequenceDiagram
    actor Pasajero
    actor Conductor
    participant Frontend
    participant API as FastAPI
    participant Service as Servicio de pagos
    participant DB as SQLite de desarrollo
    Pasajero->>Frontend: Solicita QR para una ruta
    Frontend->>API: POST /api/v1/demo/account/qr · bearer
    API->>Service: Verifica saldo, ruta y tarifa
    Service->>DB: Guarda QR activo y expiración
    Service-->>API: Token HMAC con vigencia ≤15 min
    API-->>Frontend: Token y SVG escaneable
    Conductor->>Frontend: Escanea o pega el token
    Frontend->>API: POST /api/v1/driver/qr/validate · bearer DRIVER
    API->>Service: Verifica firma, expiración, ruta y turno
    Service->>DB: Consume QR, debita saldo y asocia viaje al turno
    API-->>Frontend: Recibo demo y totales actualizados
    Conductor->>API: POST /api/v1/driver/shift/close · cash_counted
    API->>Service: Consolida recaudo y diferencia de efectivo
    Service->>DB: Persiste cierre de turno
```

La secuencia QR requiere conectividad con la API. HMAC sirve para este validador online; no se debe entregar el secreto a dispositivos offline.
