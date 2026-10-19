# Interfaz QrPass

Aplicación adaptable a móviles y PWA hecha con HTML, CSS y JavaScript nativos. No necesita compilación ni paquetes de interfaz. Se conecta con la API de demostración; no procesa dinero real.

## Ejecutar localmente

1. Inicia la API siguiendo las instrucciones de [`backend/`](../backend/README.md). Su dirección predeterminada es `http://127.0.0.1:8000`.
2. Desde la raíz del proyecto, sirve esta carpeta:

   ```powershell
   py -m http.server 5500 --directory frontend
   ```

3. Abre `http://127.0.0.1:5500` e inicia sesión con una cuenta de demostración o registra una cuenta de pasajero.
4. La documentación interactiva de la API está en `http://127.0.0.1:8000/docs`.

La dirección de la API puede establecerse con `window.QRPASS_API_BASE_URL` antes de cargar `app.js`; el origen del sitio debe estar permitido en `QR_PASS_CORS_ORIGINS`.

## Archivos

- `index.html`: estructura de la página y recursos de inicio.
- `styles.css`: diseño y adaptación a pantallas pequeñas.
- `app.js`: inicio de sesión, navegación y flujos de pasajero y conductor.
- `cache.js`: almacenamiento de recursos para la PWA.
- `manifest.webmanifest`: nombre, iconos e instalación de la aplicación.
- `iconos/`: recursos gráficos de la PWA y del acceso móvil.

## Flujos y límites

El servidor asigna y verifica roles; solo una cuenta con `DRIVER` puede usar las funciones de conductor. El pasajero consulta saldo e historial, simula pagos y recargas, escanea el QR firmado que muestra el bus y solicita un transbordo si abordó la ruta equivocada. El conductor puede iniciar el turno asignado, mostrar el QR temporal de abordaje, registrar recaudos simulados y consultar los cierres persistidos.

Las operaciones financieras y los resultados son ficticios. La PWA cachea la interfaz, pero **no permite autorizar viajes, cobrar o sincronizar movimientos sin conexión**. Los QR actuales dependen de la API para verificar la firma.

TLS 1.3, operación productiva, compatibilidad certificada con Android 8+, pagos/POS, regulación sectorial y revisión jurídica de privacidad siguen pendientes. Consulta la [trazabilidad de requisitos](../backend/docs/trazabilidad.md) para conocer el alcance y las dependencias.

No uses información personal ni financiera real.
