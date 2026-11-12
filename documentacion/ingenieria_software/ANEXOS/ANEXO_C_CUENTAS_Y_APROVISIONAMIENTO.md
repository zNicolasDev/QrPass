# Anexo C. Cuentas y aprovisionamiento

QrPass no crea cuentas automáticamente al iniciar la base de datos. Los pasajeros se registran desde la interfaz y las cuentas de conductor y administración se crean con la gestión del backend.

## Comandos

```powershell
# Esquema y roles del sistema
python -m app.management init

# Rutas y tarifas del catálogo maestro
python -m app.management import-catalog

# Conductor con roles PASSENGER y DRIVER
python -m app.management create-driver --nombre "Conductor QrPass" --correo conductor@qrpass.com --contrasena "Clave-Segura-2026" --licencia LIC-001 --ruta 24 --placa ABC123

# Administrador con roles PASSENGER y ADMIN
python -m app.management create-admin --nombre "Administrador QrPass" --correo admin@qrpass.com --contrasena "Clave-Segura-2026"

# Resumen de datos persistidos
python -m app.management status
```

## Roles

| Rol | Uso |
|---|---|
| `PASSENGER` | Registro, billetera, pagos, historial y traspasos. |
| `DRIVER` | Turno asignado, QR del bus, registro de recaudos y cierre. También conserva el espacio pasajero. |
| `ADMIN` | Consulta de métricas globales de recaudo. También conserva el espacio pasajero. |

Las contraseñas deben tener al menos 12 caracteres. Si se omite `--contrasena`, el comando la solicita de forma interactiva. El correo se usa como nombre de usuario.
