# QrPass

Prototipo web y API para consultar viajes y explorar el recaudo del transporte público de Ibagué.

## Carpetas principales

- [`frontend/`](./frontend/): interfaz adaptable y PWA para pasajeros y conductores.
- [`backend/`](./backend/): API FastAPI, autenticación por roles, reglas, base local y pruebas.
- [`backend/app/models/`](./backend/app/models/): modelos SQLAlchemy activos y relaciones de persistencia.
- [`backend/app/dtos/`](./backend/app/dtos/): contratos Pydantic para validar solicitudes y respuestas de la API.
- [`prototipo.py`](./prototipo.py): aplicación de escritorio original, conservada como referencia.
- [`requisitos.pdf`](./requisitos.pdf): documento de requisitos del proyecto.

## Iniciar la API

Desde la raíz del proyecto, en PowerShell:

```powershell
Set-Location .\backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

La API queda disponible en `http://127.0.0.1:8000`; su documentación interactiva está en `http://127.0.0.1:8000/docs`.

## Iniciar la interfaz

En otra terminal, desde la raíz del proyecto:

```powershell
py -m http.server 5500 --directory frontend
```

Abre `http://127.0.0.1:5500`. La interfaz se comunica con la API local. Las cuentas, pagos, recargas, QR y operaciones de turno son de demostración; no se procesa dinero real.

## Alcance y límites

Los roles y permisos se validan en la API: las cuentas de pasajero no pueden usar las funciones protegidas del conductor. Una cuenta autorizada como conductor también tiene acceso independiente al espacio de pasajero. Para instalar la PWA en un dispositivo, publica la interfaz mediante HTTPS.

El esquema de dominio aún está en revisión y la referencia actual se documenta en [backend/docs/arquitectura.md](./backend/docs/arquitectura.md). La intención es mantener el modelo cercano a la estructura de usuarios, rutas, pagos, QR, turnos y transbordos que aparece en el boceto de base de datos.

La matriz de [trazabilidad de requisitos](./backend/docs/trazabilidad.md) distingue lo implementado en esta demostración de lo que requiere servicios externos, pruebas en dispositivos o validación del operador y de la autoridad.
