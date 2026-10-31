# ANEXO A. ESTRUCTURA DETALLADA DEL CÓDIGO

## Backend
```text
backend/app/
├── __init__.py
├── core/
│   ├── main.py
│   └── database.py
├── seguridad/
│   ├── auth.py
│   └── passwords.py
├── servicios/
│   ├── comun.py
│   ├── usuarios.py
│   ├── rutas_tarifas.py
│   ├── qr.py
│   ├── pagos.py
│   ├── viajes.py
│   ├── transbordos.py
│   ├── turnos.py
│   └── administracion.py
├── controllers/
│   ├── autenticacion.py
│   ├── conductor.py
│   ├── pasajero.py
│   ├── administracion.py
│   └── sistema.py
├── dtos/
└── models/
```
Compatibilidad: `app/main.py`, `app/database.py`, `app/auth.py`, `app/passwords.py` y `app/services.py` se mantienen como shims de reexportación.

## Frontend
```text
frontend/
├── index.html
├── app.js
├── styles.css
├── manifest.webmanifest
├── service-worker.js
├── cache.js
└── assets/
```
