# 8. DISEÑO DE INTERFAZ

## 8.1. Tecnologías Frontend
- HTML5, CSS3, JavaScript (Vanilla)
- PWA: `manifest.webmanifest`, `service-worker.js`, `cache.js`
- Comunicación con API REST vía `fetch` con token Bearer

## 8.2. Estructura
```text
frontend/
├── index.html
├── app.js
├── styles.css
├── manifest.webmanifest
├── service-worker.js
├── cache.js
└── assets/
```

## 8.3. Vistas Principales
| Vista | Descripción |
|---|---|
| Login/Registro | Autenticación y registro de pasajero |
| Pasajero - Inicio | Saldo, accesos a recarga, pago, QR, historial |
| Pasajero - Recarga | Monto con clave de idempotencia |
| Pasajero - Pago Manual | Ruta, método, destino si aplica |
| Pasajero - Escanear QR | Pago con saldo escaneando QR del bus |
| Conductor - Panel | Iniciar/cerrar turno, generar QR |
| Historial | Pagos y viajes con detalle |

## 8.4. Consideraciones
- Diseño responsive
- Tokens almacenados en cliente
- Mensajes coherentes con respuestas API
- Soporte PWA para instalación móvil
