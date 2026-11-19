# Anexo C. Cuentas y aprovisionamiento

QrPass no crea cuentas automáticamente al iniciar la base de datos. Los pasajeros se registran desde la interfaz y las cuentas de conductor se crean con la gestión del backend.

## Comandos

```powershell
# Esquema de la base
python -m app.management init

# Catálogo inicial desde un archivo externo (roles, perfiles, rutas y tarifas)
python -m app.management load-catalog --archivo .\catalogo.json

# Aplicar el catálogo guardado a las tablas de rutas y tarifas
python -m app.management import-catalog

# Conductor con roles PASSENGER y DRIVER
python -m app.management create-driver --nombre "Conductor QrPass" --correo conductor@qrpass.com --contrasena "Clave-Segura-2026" --licencia LIC-001 --ruta 24 --placa ABC123

# Resumen de datos persistidos
python -m app.management status
```

## Roles

| Rol | Uso |
|---|---|
| `PASSENGER` | Registro, billetera, pagos, historial y traspasos. |
| `DRIVER` | Turno asignado, QR del bus, registro de recaudos y cierre. También conserva el espacio pasajero. |

Las métricas globales y su panel quedan como mejora futura. El conductor consulta el resumen y el historial de sus propios turnos. Las contraseñas deben tener al menos 12 caracteres. Si se omite `--contrasena`, el comando la solicita de forma interactiva. El correo se usa como nombre de usuario.
