const ACCESS_TOKEN_KEY = "qrpass-access-token-v1";
const SESSION_EXPIRY_KEY = "qrpass-session-expiry-v1";
// En HTTPS (túnel) la API se pide por el mismo origen, a través del proxy de Apache (.htaccess),
// para que el navegador no bloquee contenido mixto. En HTTP local se usa el puerto 8000 directo.
const API_BASE_URL = globalThis.QRPASS_API_BASE_URL ?? (
  window.location.protocol === "https:"
    ? new URL("./api/v1", window.location.href).href
    : `http://${window.location.hostname || "127.0.0.1"}:8000/api/v1`
);

// Comparte token, cabeceras y errores para que cada página no implemente su propio cliente HTTP.
async function requestApi(path, options = {}) {
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");
  if (options.body) headers.set("Content-Type", "application/json");

  const token = sessionStorage.getItem(ACCESS_TOKEN_KEY);
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  } catch {
    throw new Error("No se pudo conectar con QrPass. Comprueba que la API esté iniciada.");
  }

  let payload;
  try {
    payload = await response.json();
  } catch {
    throw new Error(`La API respondió con un formato inesperado (HTTP ${response.status}).`);
  }
  if (!response.ok) {
    let detail = "";
    if (Array.isArray(payload.detail)) {
      detail = payload.detail.map((issue) => (typeof issue === "string" ? issue : issue.msg)).join(" ");
    } else if (typeof payload.detail === "string") {
      detail = payload.detail;
    }
    if (Array.isArray(payload.errores)) {
      const campos = payload.errores.map((item) => item.mensaje || item.msg).filter(Boolean).join(" ");
      if (campos) detail = detail ? `${detail} ${campos}` : campos;
    }
    const error = new Error(detail || `La solicitud falló (HTTP ${response.status}).`);
    error.status = response.status;
    throw error;
  }
  return payload;
}

window.QrPassApi = Object.freeze({
  ACCESS_TOKEN_KEY,
  SESSION_EXPIRY_KEY,
  API_BASE_URL,
  request: requestApi,
});
