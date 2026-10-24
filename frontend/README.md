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

## Cobertura de la interfaz frente a los requisitos

La interfaz permite recorrer los flujos de demostración de registro e inicio de sesión (RF-01 y RF-02), pagos (RF-03), tarifa vigente (RF-05), registro de efectivo y cierre de turno (RF-06, RF-10 y RF-11), recarga (RF-07), transbordo (RF-08) e historial con comprobantes y detalle (RF-09). El registro unificado muestra pagos, recargas, viajes transferidos y, cuando la API lo devuelve, el saldo anterior y posterior.

RF-02 usa la ruta que el servidor asignó al conductor; la interfaz todavía no permite escoger una ruta entre varias. RF-04 requiere aclarar el sentido del QR: el documento pide que lo genere el pasajero, mientras que el contrato actual hace que el bus muestre un QR y que el pasajero lo escanee. La interfaz sigue el contrato disponible; no inventa códigos que la API no pueda validar.

El registro enlaza un aviso de privacidad de demostración que describe los datos, su uso y almacenamiento. No existe todavía un panel administrativo o de auditoría, y ese aviso no reemplaza una política aprobada ni cubre las obligaciones legales de producción.

Esta cobertura es de interfaz y demostración. El backend aún no integra pasarela bancaria ni POS, las recargas son ficticias y el prototipo no autoriza pagos o sincroniza movimientos sin conexión. RNF-02 y RNF-05 necesitan mediciones en dispositivos reales; TLS 1.3 y la escalabilidad dependen del despliegue; los aspectos de dominio y privacidad necesitan validación externa. Consulta la [trazabilidad completa](../documentacion/trazabilidad.md) para los límites técnicos y operativos.

## Flujos y límites

El servidor asigna y verifica roles; solo una cuenta con `DRIVER` puede usar las funciones de conductor. El pasajero consulta saldo e historial, simula pagos y recargas, escanea el QR firmado que muestra el bus y solicita un transbordo si abordó la ruta equivocada. El conductor puede iniciar el turno asignado, mostrar el QR temporal de abordaje, registrar recaudos simulados y consultar los cierres persistidos.

Las operaciones financieras y los resultados son ficticios. La PWA cachea la interfaz, pero **no permite autorizar viajes, cobrar o sincronizar movimientos sin conexión**. Los QR actuales dependen de la API para verificar la firma.

TLS 1.3, operación productiva, compatibilidad certificada con Android 8+, pagos/POS, regulación sectorial y revisión jurídica de privacidad siguen pendientes. Consulta la [trazabilidad de requisitos](../documentacion/trazabilidad.md) para conocer el alcance y las dependencias.

No uses información personal ni financiera real.
