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

### Crear cuentas de conductor

Los pasajeros se registran desde la interfaz. Las cuentas de conductor se crean por CLI. Incluye `--ruta` y `--placa` para dejar una asignación preparada:

```powershell
python -m app.management create-driver --nombre "Conductor QrPass" --correo conductor@qrpass.com --contrasena "Clave-Segura-2026" --licencia LIC-001 --ruta 24 --placa ABC123
python -m app.management status
```

Las estadísticas globales quedan como mejora futura; actualmente el conductor consulta el recaudo de sus propios turnos.

## Iniciar la interfaz

En otra terminal, desde la raíz del proyecto:

```powershell
py -m http.server 5500 --directory frontend
```

Abre `http://127.0.0.1:5500`. La interfaz se comunica con la API local. Los pagos se realizan con el saldo de la billetera QrPass; no se procesa dinero real ni se conectan pasarelas bancarias.

## Prueba HTTPS desde el celular

Haz doble clic en `iniciar.bat`. El backend servira tambien el frontend y Cloudflare Tunnel mostrara un enlace HTTPS temporal; abre ese enlace en el celular y manten las ventanas del tunel y de la API abiertas. La interfaz usa una ruta relativa para llamar a la API cuando se carga por HTTPS, asi que ambas quedan en el mismo origen y no requieren una regla CORS para el subdominio aleatorio.

El enlace de Quick Tunnel es publico, cambia al reiniciar y solo funciona mientras el tunel siga abierto. Usalo unicamente para pruebas y no con datos sensibles.

## Alcance y límites

Los roles y permisos se validan en la API: las cuentas de pasajero no pueden usar las funciones protegidas del conductor. Una cuenta autorizada como conductor también tiene acceso independiente al espacio de pasajero. Para instalar la PWA en un dispositivo, publica la interfaz mediante HTTPS.

El esquema de dominio se documenta en [documentacion/arquitectura.md](./documentacion/arquitectura.md). El modelo cubre usuarios, rutas, pagos, QR, turnos y transbordos, y la información se persiste en SQLite mediante SQLAlchemy.

La matriz de [trazabilidad de requisitos](./documentacion/trazabilidad.md) distingue lo implementado de lo que requiere servicios externos, pruebas en dispositivos o validación del operador y de la autoridad.
