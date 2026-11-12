# QrPass

Plataforma web y API para gestionar viajes y el recaudo del transporte público de Ibagué con la billetera QrPass.

## Estructura principal del proyecto

- [`frontend/`](./frontend/): Interfaz adaptable y PWA para pasajeros y conductores.
- [`backend/`](./backend/): API FastAPI, autenticación por roles, reglas de negocio, base local y pruebas.
- [`documentacion/`](./documentacion/): Especificación de requisitos (`requisitos.pdf`), arquitectura, matriz de trazabilidad y diagramas UML.

## Iniciar la API

Desde la raíz del proyecto, en PowerShell:

```powershell
Set-Location .\backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m app.management init
python -m app.management import-catalog
python -m uvicorn app.core.main:app --reload
```

`init` crea el esquema y los roles del sistema. `import-catalog` carga las rutas y tarifas desde `app/datos_maestros/rutas_tarifas.json`. La API queda disponible en `http://127.0.0.1:8000`; su documentación interactiva está en `http://127.0.0.1:8000/docs`.

### Crear cuentas operativas

Los pasajeros se registran desde la interfaz. Las cuentas de conductor y administración se crean con la gestión de QrPass:

```powershell
python -m app.management create-driver --nombre "Conductor QrPass" --correo conductor@qrpass.com --contrasena "Clave-Segura-2026" --licencia LIC-001 --ruta 24 --placa ABC123
python -m app.management create-admin --nombre "Administrador QrPass" --correo admin@qrpass.com --contrasena "Clave-Segura-2026"
python -m app.management status
```

## Iniciar la interfaz

En otra terminal, desde la raíz del proyecto:

```powershell
py -m http.server 5500 --directory frontend
```

Abre `http://127.0.0.1:5500`. La interfaz se comunica con la API local. Los pagos se realizan con el saldo de la billetera QrPass; no se procesa dinero real ni se conectan pasarelas bancarias.

## Alcance y límites

Los roles y permisos se validan en la API: las cuentas de pasajero no pueden usar las funciones protegidas del conductor, y las métricas globales requieren el rol `ADMIN`. Una cuenta autorizada como conductor también tiene acceso independiente al espacio de pasajero. Para instalar la PWA en un dispositivo, publica la interfaz mediante HTTPS.

El esquema de dominio se documenta en [documentacion/arquitectura.md](./documentacion/arquitectura.md). El modelo cubre usuarios, rutas, pagos, QR, turnos y transbordos, y la información se persiste en SQLite mediante SQLAlchemy.

La matriz de [trazabilidad de requisitos](./documentacion/trazabilidad.md) distingue lo implementado de lo que requiere servicios externos, pruebas en dispositivos o validación del operador y de la autoridad.
