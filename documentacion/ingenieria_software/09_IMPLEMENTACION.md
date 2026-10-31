# 9. IMPLEMENTACIÓN

## 9.1. Tecnologías Utilizadas
| Componente | Tecnología | Detalle |
|---|---|---|
| Backend | FastAPI | API REST |
| ORM | SQLAlchemy 2.x | Mapped/mapped_column |
| Validación | Pydantic v2 | Esquemas entrada/salida |
| Servidor | Uvicorn | ASGI |
| BD | SQLite | Desarrollo/demo |
| Frontend | HTML/CSS/JS Vanilla | PWA |
| Testing | Pytest | Suite automatizada |

## 9.2. Convenciones
- Nombres de dominio en español cuando aplica
- DTOs separados de modelos ORM
- `response_model` en endpoints
- `ErrorDominio` para reglas de negocio
- Transacciones controladas desde servicios
- Claves foráneas activas

## 9.3. Módulos Clave
| Módulo | Función |
|---|---|
| `main.py` | Bootstrap, lifespan, CORS, exception handler, routers |
| `database.py` | Engine, SessionLocal, `initialize()`, seed demo |
| `auth.py` | Tokens Bearer, `UsuarioAutenticado` |
| `passwords.py` | Hash/verify contraseñas |
| `services.py` | Casos de uso, validaciones, cálculos, transacciones |
| `controllers/*` | Endpoints HTTP por dominio |
| `models/*` | Mapeo ORM |
| `dtos/*` | Contratos entrada/salida |
