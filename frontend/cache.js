const CACHE_NAME = "qrpass-demo-shell-v12";
const APP_FILES = [
  "./index.html",
  "./styles.css",
  "./app.js",
  "./manifest.webmanifest",
  "./iconos/qrpass.svg",
  "./iconos/qrpass-192.png",
  "./iconos/qrpass-512.png",
  "./iconos/apple-touch-icon.png",
];

// La caché mantiene abierta la carcasa de la app si falta internet; no guarda
// pagos ni autoriza viajes. Para eso siempre hace falta una respuesta del servidor.
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(APP_FILES))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => Promise.all(
        cacheNames
          .filter((cacheName) => cacheName.startsWith("qrpass-demo-shell-") && cacheName !== CACHE_NAME)
          .map((cacheName) => caches.delete(cacheName)),
      ))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;

  const requestUrl = new URL(request.url);
  if (requestUrl.origin !== self.location.origin) return;

  if (request.mode === "navigate") {
    // Primero intentamos mostrar la versión nueva; si no hay conexión,
    // ofrecemos la última pantalla descargada en vez de una página vacía.
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.ok) {
            const responseCopy = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put("./index.html", responseCopy));
          }
          return response;
        })
        .catch(async () => (await caches.match("./index.html")) || Response.error()),
    );
    return;
  }

  event.respondWith(
    // En el desarrollo actual la API vive en otro origen y no pasa por aquí.
    // Si interfaz y API comparten origen más adelante, excluye sus respuestas
    // antes de guardar recursos para no conservar datos de una persona.
    caches.match(request)
      .then((cachedResponse) => cachedResponse || fetch(request).then((response) => {
        if (!response.ok) return response;
        const responseCopy = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(request, responseCopy));
        return response;
      })),
  );
});
