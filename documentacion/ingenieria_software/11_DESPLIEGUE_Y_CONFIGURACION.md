# 11. DESPLIEGUE Y CONFIGURACIÓN

## 11.1. Requisitos
- Python 3.10+
- Navegador moderno
- PowerShell

## 11.2. Variables de Entorno
| Variable | Requerida | Descripción |
|---|---|---|
| `QR_PASS_AUTH_SECRET` | Sí (prod) | Secreto para firmar tokens |
| `QR_PASS_DATABASE_URL` | Opcional | URL SQLAlchemy (default SQLite) |
| `QR_PASS_ENV` | Opcional | `production` activa validaciones estrictas |
| `QR_PASS_DEMO_PASSENGER_PASSWORD` | Opcional | Contraseña demo pasajero |
| `QR_PASS_DEMO_DRIVER_PASSWORD` | Opcional | Contraseña demo conductor |
| `QR_PASS_CORS_ORIGINS` | Opcional | Orígenes permitidos separados por coma |

## 11.3. Ejecución Local

### Backend
```powershell
Set-Location .\backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.core.main:app --reload
```
- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`

### Frontend
```powershell
py -m http.server 5500 --directory frontend
```
- Frontend: `http://127.0.0.1:5500`

## 11.4. Inicialización
En `lifespan` de `main.py`, `database.initialize()` ejecuta `create_all()`, migraciones ad-hoc SQLite y seed (roles, usuarios demo, empresa/vehículo, tarifas, turno).
