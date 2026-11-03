# Interfaz QrPass

Aplicación adaptable a móviles y PWA hecha con HTML, CSS y JavaScript nativos. No necesita compilación ni paquetes de interfaz. Se conecta con la API de plataforma; no procesa dinero real.

## Ejecutar localmente

1. Inicia la API siguiendo las instrucciones de [`backend/`](../backend/README.md). Su dirección predeterminada es `http://127.0.0.1:8000`.
2. Desde la raíz del proyecto, sirve esta carpeta:

   ```powershell
   py -m http.server 5500 --directory frontend
   ```

3. Abre `http://127.0.0.1:5500` e inicia sesión con una cuenta de plataforma o registra una cuenta de pasajero.
4. La documentación interactiva de la API está en `http://127.0.0.1:8000/docs`.

La dirección de la API puede establecerse con `window.QRPASS_API_BASE_URL` antes de cargar `api.js`; el origen del sitio debe estar permitido en `QR_PASS_CORS_ORIGINS`.

## Archivos

- `index.html`: punto de entrada que valida la sesión y dirige al espacio elegido.
- `login.html`: página independiente de inicio de sesión y registro.
- `pasajero.html` / `pasajero.css`: acceso y presentación específica del espacio pasajero.
- `conductor.html` / `conductor.css`: acceso y presentación específica del espacio conductor.
- `workspace.html`: estructura compartida para no duplicar el menú, las ventanas y la navegación.
- `workspace-loader.js`: carga la estructura compartida y luego inicia la lógica del espacio.
- `index.js` / `index.css`: selección de perfil y pantalla breve de entrada.
- `api.js`: cliente HTTP compartido, autorización de sesión y manejo de errores de API.
- `login.js`: envío de credenciales, registro y aviso de privacidad.
- `app.js`: navegación autenticada y flujos funcionales de pasajero/conductor.
- `styles.css` y `premium.css`: estilos compartidos y tema del espacio autenticado.
- `login.css`: presentación específica de la página de acceso.
- `cache.js`: almacenamiento de recursos para la PWA.
- `manifest.webmanifest`: nombre, iconos e instalación de la aplicación.
- `iconos/`: recursos gráficos de la PWA y del acceso móvil.

## Contrato de integración

La tabla de los tres módulos principales (autenticación, pasajero/pagos y conductor) documenta pantalla, requisito funcional, método, endpoint, JSON y forma de respuesta en [`documentacion/ingenieria_software/CONTRATO_INTEGRACION_FRONTEND.md`](../documentacion/ingenieria_software/CONTRATO_INTEGRACION_FRONTEND.md).

## Flujos y límites

El servidor asigna y verifica roles; solo una cuenta con `DRIVER` puede usar las funciones de conductor. El pasajero consulta saldo e historial, simula pagos y recargas, escanea el QR firmado que muestra el bus y solicita un transbordo si abordó la ruta equivocada. El conductor puede iniciar el turno asignado, mostrar el QR temporal de abordaje, registrar recaudos simulados y consultar los cierres persistidos.

Las operaciones financieras y los resultados son ficticios. La PWA cachea la interfaz, pero **no permite autorizar viajes, cobrar o sincronizar movimientos sin conexión**. Los QR actuales dependen de la API para verificar la firma.

TLS 1.3, operación productiva, compatibilidad certificada con Android 8+, pagos/POS, regulación sectorial y revisión jurídica de privacidad siguen pendientes. Consulta la [trazabilidad de requisitos](../documentacion/trazabilidad.md) para conocer el alcance y las dependencias.

No uses información personal ni financiera real.
