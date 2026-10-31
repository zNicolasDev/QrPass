# 5. ARQUITECTURA DEL SISTEMA

## 5.1. Arquitectura General
QrPass sigue una arquitectura **cliente-servidor** con separación entre frontend y backend.

```text
[Frontend PWA (HTML/CSS/JS)] --HTTP/JSON--> [FastAPI API REST /api/v1]
                                                |-- Controllers
                                                |-- Services
                                                |-- Models (ORM SQLAlchemy)
                                                |-- SQLite
```

## 5.2. Estructura del Backend
```text
backend/app/
├── main.py
├── database.py
├── auth.py
├── passwords.py
├── services.py
├── controllers/
├── dtos/
└── models/
```

## 5.3. Flujo de Petición
1. Cliente envía petición HTTP a `/api/v1/...`
2. FastAPI enruta al controlador
3. Dependencias inyectan `Session` y `UsuarioAutenticado` si aplica
4. DTO valida payload/params
5. Controlador delega a `services.py`
6. Servicio aplica reglas, consulta/actualiza ORM
7. Transacción commit/rollback
8. Respuesta serializada con `response_model`
9. FastAPI retorna JSON

## 5.4. Manejo de Errores
- Validación Pydantic → `422 Unprocessable Entity`
- Errores de negocio (`ErrorDominio`) → manejador global en `main.py` retorna `JSONResponse` con `status_code` y `detail`. Para `401` añade `WWW-Authenticate: Bearer`
- Errores de autenticación/autorización → gestionados en `app/auth.py`
