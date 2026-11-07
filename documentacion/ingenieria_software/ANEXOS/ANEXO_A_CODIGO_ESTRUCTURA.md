# Anexo A. Estructura del código

```
backend/app/
  core/          # main.py, database.py
  controllers/   # sistema, autenticacion, pasajero, conductor, administracion
  dtos/          # contratos Pydantic
  models/        # entidades SQLAlchemy
  seguridad/     # auth, passwords
  servicios/     # reglas de negocio por responsabilidad
frontend/
  index.html, app.js, styles.css, premium.css, cache.js, manifest.webmanifest, iconos/
documentacion/
  ingenieria_software/  # esta documentación
```