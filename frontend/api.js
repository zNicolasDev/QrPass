const ACCESS_TOKEN_KEY = "qrpass-access-token-v1";
const SESSION_EXPIRY_KEY = "qrpass-session-expiry-v1";
const API_BASE_URL = globalThis.QRPASS_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

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
    const detail = Array.isArray(payload.detail)
      ? payload.detail.map((issue) => issue.msg).join(" ")
      : payload.detail;
    const error = new Error(detail || `La solicitud falló (HTTP ${response.status}).`);
    error.status = response.status;
    throw error;
  }
  return payload;
}

window.QrPassApi = Object.freeze({
  ACCESS_TOKEN_KEY,
  SESSION_EXPIRY_KEY,
  request: requestApi,
});
