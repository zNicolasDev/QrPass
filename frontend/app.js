// La pantalla sigue el recorrido de la persona; el servidor conserva las
// decisiones y el historial. Si algo cambia dinero o un viaje, se confirma allí.
// Arrancamos con lo que la interfaz necesita y guardamos aquí su estado.
const apiClient = window.QrPassApi;
const apiRequest = apiClient.request;

const content = document.querySelector("#app-content");
const modal = document.querySelector("#app-modal");
const modalContent = document.querySelector("#modal-content");
const sidebar = document.querySelector("#sidebar");
const sidebarBackdrop = document.querySelector("#sidebar-backdrop");
const installButton = document.querySelector("#install-button");
const connectionStatus = document.querySelector("#connection-status");
const connectionLabel = document.querySelector("#connection-label");
const toastRegion = document.querySelector("#toast-region");
let currentView = "inicio";
let currentProfile = "pasajero";
let authenticatedUser = null;
let sessionExpiryTimer = null;
let activeFilter = "todos";
let activeBusQr = null;
// Hora oficial de la app: todas las fechas se muestran en hora de Colombia (Bogotá),
// sin importar la zona horaria que tenga configurada el celular.
const APP_TIME_ZONE = "America/Bogota";
// El QR del bus cambia solo: el servidor lo renueva a los 60 s o cuando alguien lo usa,
// y la pantalla del conductor lo consulta cada pocos segundos para mostrar el nuevo.
const BUS_QR_POLL_SECONDS = 3;
let busQrTimer = null;
let busQrTick = 0;
let busQrSyncing = false;
// Los pagos del turno se consultan con más frecuencia que el QR para no perder ningún registro.
const DRIVER_PAYMENTS_POLL_MS = 2000;
let driverPaymentsTimer = null;
let driverPaymentsSyncing = false;
let driverPaymentsSignature = "";

let serverTimeOffsetMs = 0;
let driverClockTimer = null;

async function syncServerTime() {
  try {
    const response = await apiRequest("/time");
    const serverNow = new Date(response.server_time).getTime();
    serverTimeOffsetMs = serverNow - Date.now();
    const synced = new Date(Date.now() + serverTimeOffsetMs);
    showToast(`Hora sincronizada: ${formatTime(synced)} · ${formatDate(synced)}`);
  } catch (error) {
    showToast(error.message || "No se pudo sincronizar la hora.", true);
  }
  renderCurrentView();
}
let selectedPaymentMethod = "saldo";
let deferredInstallPrompt = null;
let routeCatalog = [];
let currentFare = 0;
let currentDayType = "weekday";
let fareCatalog = [];
let driverAssignment = null;
let driverAssignments = [];
let selectedDriverRouteId = null;
let activeCameraStream = null;
let scanLoopTimer = null;

// Herramientas compartidas: formato, seguridad y comunicación con el servidor.
function createIdempotencyKey() {
  // Una misma acción conserva su clave mientras se reintenta; al empezar otra
  // acción se crea otra. Así un toque lento no se convierte en dos cobros.
  return globalThis.crypto?.randomUUID?.()
    ?? `qrpass-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

// Presenta valores de dinero en pesos colombianos, sin decimales.
function money(value) {
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(value);
}

// Escapa texto antes de insertarlo en una plantilla HTML para que se trate
// como texto y no como etiquetas o atributos.
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[character]);
}

function getFare() {
  return currentFare;
}

// Destinos con tarifa propia para una ruta (por ejemplo la 48), en el orden
// que entrega la API y sin repetirse entre días de semana y festivos.
function routeDestinations(routeId) {
  const names = fareCatalog
    .filter((fare) => fare.route_id === routeId && fare.destination)
    .map((fare) => fare.destination);
  return [...new Set(names)];
}

// Valor vigente de una ruta; con destino usa la tarifa de ese destino.
// El valor definitivo siempre lo calcula el servidor al registrar el pago.
function getFareFor(routeId, destination) {
  const match = fareCatalog.find((fare) => fare.route_id === routeId
    && (fare.destination ?? null) === (destination || null));
  return match?.amount ?? currentFare;
}

function hasProfileRole(profile) {
  if (profile !== "pasajero" && profile !== "conductor") return false;
  const role = profile === "conductor" ? "DRIVER" : "PASSENGER";
  return authenticatedUser?.roles.includes(role) ?? false;
}

function mapTripFromApi(trip) {
  const methodLabels = {
    wallet: "Saldo QR",
    cash: "Efectivo",
    card_debit: "Tarjeta débito",
    card_credit: "Tarjeta crédito",
  };
  return {
    route: trip.route_name,
    method: methodLabels[trip.method] ?? trip.method,
    amount: trip.amount,
    code: `VIA-${trip.trip_id}`,
    tripId: trip.trip_id,
    transferred: Boolean(trip.transferred_to),
    transferredTo: trip.transferred_to,
    createdAt: trip.created_at,
  };
}

function mapPaymentFromApi(payment) {
  const methodLabels = {
    wallet: "Saldo QR",
    cash: "Efectivo",
    card_debit: "Tarjeta débito",
    card_credit: "Tarjeta crédito",
  };
  return {
    id: String(payment.payment_id),
    type: payment.movement_type,
    method: payment.movement_type === "top_up"
      ? "Billetera"
      : methodLabels[payment.method] ?? payment.method,
    amount: payment.amount,
    balanceBefore: payment.balance_before,
    balanceAfter: payment.balance_after,
    route: payment.route_name,
    tripId: payment.trip_id,
    status: payment.status === "completed" ? "Registrado" : payment.status,
    createdAt: payment.created_at,
    reference: `PAGO-${payment.payment_id}`,
  };
}

async function refreshPassengerData() {
  // Al volver de una operación, reconstruimos saldo e historial desde el
  // servidor: la memoria de esta pestaña no es el registro oficial.
  // Saldo e historial se piden en paralelo para que la pantalla muestre datos actuales.
  const [account, trips, history] = await Promise.all([
    apiRequest("/account"),
    apiRequest("/trips"),
    apiRequest("/payments/history"),
  ]);
  state = {
    balance: account.wallet_balance,
    payments: history.map(mapPaymentFromApi),
    trips: trips.flatMap((trip) => {
      const movement = mapTripFromApi(trip);
      if (!trip.transferred_to) return [movement];
      return [movement, {
        ...movement,
        route: trip.transferred_to,
        method: `Traspaso desde ${trip.route_name}`,
        amount: 0,
        code: `TRASP-${trip.trip_id}`,
        transferred: false,
      }];
    }),
  };
}

function mapShiftFromApi(shift) {
  const methodLabels = { cash: "Efectivo", wallet: "QR / saldo", card_debit: "Tarjeta", card_credit: "Tarjeta" };
  return {
    reference: `TUR-${shift.shift_id}`,
    route: shift.route_name,
    vehicle: shift.vehicle_plate,
    routeId: shift.route_id,
    shiftId: shift.shift_id,
    startedAt: shift.starts_at,
    endedAt: shift.ends_at,
    cashExpected: shift.cash_total,
    cashCounted: shift.cash_counted,
    cashDifference: shift.cash_difference,
    total: shift.cash_total + shift.qr_total + shift.card_total,
    entries: shift.entries.map((entry) => ({
      reference: `REC-${entry.payment_id}`,
      method: methodLabels[entry.method] ?? entry.method,
      amount: entry.amount,
      createdAt: entry.created_at,
    })),
    totals: shift,
  };
}

async function refreshDriverShift() {
  const shift = await apiRequest("/driver/shift");
  driverState.activeShift = mapShiftFromApi(shift);
  driverPaymentsSignature = driverPaymentsSignatureOf(driverState.activeShift);
  const qr = await apiRequest("/driver/shift/qr", { method: "POST" });
  activeBusQr = { image: qr.image_data_uri, expiresAt: new Date(qr.expires_at), token: qr.token };
}

async function refreshDriverAssignments() {
  try {
    const list = await apiRequest("/driver/assignments");
    driverAssignments = Array.isArray(list) ? list : [list];
  } catch (error) {
    if (error.status !== 404) throw error;
    driverAssignments = [];
  }
  if (driverAssignments.length) {
    const preferred = selectedDriverRouteId
      ? driverAssignments.find((item) => item.route_id === selectedDriverRouteId)
      : null;
    driverAssignment = preferred ?? driverAssignments[0];
    selectedDriverRouteId = driverAssignment.route_id;
  } else {
    driverAssignment = null;
  }
}

// Texto del contador que ve el conductor debajo del QR.
function busQrCountdownText() {
  if (!activeBusQr) return "";
  const seconds = Math.ceil((activeBusQr.expiresAt.getTime() - Date.now()) / 1000);
  return seconds > 0 ? `Se actualiza en ${seconds} s` : "Actualizando el código…";
}

// Parte de la pantalla del conductor que cambia cuando llega un QR nuevo.
function renderBusQrBlock(shift) {
  if (!activeBusQr) return "<p>El código QR aparecerá aquí cuando el turno esté listo.</p>";
  return `<img class="qr-real-image" src="${activeBusQr.image}" alt="Código QR para pagar el pasaje de la ruta ${escapeHtml(shift.route)}" /><p class="bus-qr-countdown" id="bus-qr-countdown" role="timer" aria-live="off">${escapeHtml(busQrCountdownText())}</p><div class="qr-token-row"><label for="bus-qr-token">Código completo para compartir manualmente</label><textarea class="qr-token-full" id="bus-qr-token" rows="4" readonly spellcheck="false">${escapeHtml(activeBusQr.token)}</textarea><button class="button button-outline button-small" type="button" data-action="copy-qr-token">Copiar código completo</button></div>`;
}

function paintBusQr() {
  // Cambia solo el recuadro del QR; así no se pierde lo que el conductor esté escribiendo más abajo.
  const holder = document.querySelector("#bus-qr-live");
  if (!holder || !driverState.activeShift) return;
  holder.innerHTML = renderBusQrBlock(driverState.activeShift);
}

function updateBusQrCountdown() {
  const label = document.querySelector("#bus-qr-countdown");
  if (label && activeBusQr) label.textContent = busQrCountdownText();
}

async function syncBusQr() {
  // Pregunta al servidor cuál es el QR vigente. Si el anterior venció (60 s) o ya lo usó un pasajero,
  // el servidor entrega uno nuevo y aquí se reemplaza solo en pantalla.
  if (busQrSyncing || currentProfile !== "conductor" || !driverState.activeShift) return;
  if (!document.querySelector("#bus-qr-live")) return;
  busQrSyncing = true;
  try {
    const qr = await apiRequest("/driver/shift/qr", { method: "POST" });
    if (currentProfile !== "conductor" || !driverState.activeShift) return;
    const changed = qr.token !== activeBusQr?.token;
    activeBusQr = { image: qr.image_data_uri, expiresAt: new Date(qr.expires_at), token: qr.token };
    if (changed) paintBusQr();
  } catch (error) {
    // Un fallo de red momentáneo no debe molestar al conductor: se reintenta en el siguiente ciclo.
    if (error.status === 401 || error.status === 403) logout();
  } finally {
    busQrSyncing = false;
  }
}

function startBusQrAutoRefresh() {
  startDriverPaymentsAutoRefresh();
  if (busQrTimer !== null) return;
  busQrTick = 0;
  busQrTimer = window.setInterval(() => {
    busQrTick += 1;
    updateBusQrCountdown();
    const expired = activeBusQr !== null && activeBusQr.expiresAt.getTime() <= Date.now();
    if (expired || busQrTick % BUS_QR_POLL_SECONDS === 0) syncBusQr();
  }, 1000);
}

function stopBusQrAutoRefresh() {
  stopDriverPaymentsAutoRefresh();
  if (busQrTimer !== null) window.clearInterval(busQrTimer);
  busQrTimer = null;
}

// Lista de pagos que se muestra debajo del QR y se actualiza sola durante el turno.
function renderDriverLivePayments(entries) {
  const count = entries.length;
  const total = entries.reduce((sum, entry) => sum + entry.amount, 0);
  const rows = [...entries].reverse().map((entry) => `<li class="driver-live-payment">
    <span class="driver-live-time">${escapeHtml(formatTime(new Date(entry.createdAt)))}</span>
    <span class="payment-tag">${escapeHtml(entry.method)}</span>
    <strong>${money(entry.amount)}</strong>
    <small>${escapeHtml(entry.reference)}</small>
  </li>`).join("");
  return `<div class="driver-live-head"><h3>Pagos recibidos</h3><span class="driver-live-count">${count} ${count === 1 ? "pago" : "pagos"} · ${money(total)}</span></div>
    ${rows ? `<ul class="driver-live-list" aria-live="polite">${rows}</ul>` : `<p class="driver-live-empty">Aún no hay pagos. Cuando un pasajero pague, aparecerá aquí.</p>`}`;
}

function driverPaymentsSignatureOf(shift) {
  return `${shift.shiftId}|${shift.entries.map((entry) => entry.reference).join(",")}`;
}

// Actualiza solo las zonas que dependen de los pagos, sin tocar lo que el conductor esté escribiendo.
function paintDriverPayments() {
  const shift = driverState.activeShift;
  if (!shift) return;
  const entries = shift.entries;
  const sumBy = (label) => entries.filter((entry) => entry.method === label).reduce((total, entry) => total + entry.amount, 0);
  const countBy = (label) => entries.filter((entry) => entry.method === label).length;
  const plural = (n, one, many) => `${n} ${n === 1 ? one : many}`;
  const cash = sumBy("Efectivo");

  const live = document.querySelector("#driver-live-payments");
  if (live) live.innerHTML = renderDriverLivePayments(entries);

  const setText = (selector, text) => {
    const node = document.querySelector(selector);
    if (node) node.textContent = text;
  };
  setText("#driver-total-cash", money(cash));
  setText("#driver-count-cash", `${countBy("Efectivo")} registros`);
  setText("#driver-total-wallet", money(sumBy("QR / saldo")));
  setText("#driver-count-wallet", `${countBy("QR / saldo")} registros`);
  setText("#driver-total-card", money(sumBy("Tarjeta")));
  setText("#driver-count-card", `${countBy("Tarjeta")} registros`);
  setText("#driver-total-all", money(cash + sumBy("QR / saldo") + sumBy("Tarjeta")));
  setText("#driver-count-all", `${plural(entries.length, "pago registrado", "pagos registrados")}`);
  setText("#driver-boardings-count", `${plural(entries.length, "abordaje", "abordajes")} en esta jornada`);
  setText("#driver-ledger-count", `${plural(entries.length, "pago", "pagos")} en este turno`);

  const cashLabel = document.querySelector("#driver-cash-expected");
  if (cashLabel) cashLabel.textContent = money(cash);
  const cashInput = document.querySelector("#driver-cash-counted");
  if (cashInput && document.activeElement !== cashInput && cashInput.dataset.touched !== "true") {
    cashInput.value = String(cash);
  }

  const ledgerBody = document.querySelector("#driver-ledger-body");
  if (ledgerBody) {
    ledgerBody.innerHTML = [...entries].reverse().slice(0, 8).map((entry) => `<tr>
    <td><span class="driver-ledger-code">${escapeHtml(entry.reference)}</span></td>
    <td>${escapeHtml(formatTime(new Date(entry.createdAt)))}</td>
    <td><span class="payment-tag">${escapeHtml(entry.method)}</span></td>
    <td>${money(entry.amount)}</td>
  </tr>`).join("") || `<tr><td class="empty-row" colspan="4">Aún no hay pagos registrados. Al anotarlos, aparecerán aquí.</td></tr>`;
  }
}

async function syncDriverPayments() {
  // Consulta al servidor los pagos del turno (efectivo, tarjeta y QR de pasajeros) y repinta si hay cambios.
  if (driverPaymentsSyncing || currentProfile !== "conductor" || !driverState.activeShift) return;
  if (!document.querySelector("#driver-live-payments")) return;
  driverPaymentsSyncing = true;
  try {
    const shift = mapShiftFromApi(await apiRequest("/driver/shift"));
    if (currentProfile !== "conductor" || !driverState.activeShift) return;
    if (shift.shiftId !== driverState.activeShift.shiftId) return;
    const signature = driverPaymentsSignatureOf(shift);
    if (signature === driverPaymentsSignature) return;
    driverPaymentsSignature = signature;
    driverState.activeShift = shift;
    paintDriverPayments();
  } catch (error) {
    // Un fallo de red momentáneo no debe molestar al conductor: se reintenta en el siguiente ciclo.
    if (error.status === 401 || error.status === 403) logout();
  } finally {
    driverPaymentsSyncing = false;
  }
}

function startDriverPaymentsAutoRefresh() {
  if (driverPaymentsTimer !== null) return;
  driverPaymentsTimer = window.setInterval(syncDriverPayments, DRIVER_PAYMENTS_POLL_MS);
}

function stopDriverPaymentsAutoRefresh() {
  if (driverPaymentsTimer !== null) window.clearInterval(driverPaymentsTimer);
  driverPaymentsTimer = null;
}

document.addEventListener("visibilitychange", () => {
  if (!document.hidden) syncDriverPayments();
});

async function refreshDriverShiftHistory() {
  const shifts = await apiRequest("/driver/shifts/history");
  driverState.completedShifts = shifts.map(mapShiftFromApi);
}

async function activateSession(user) {
  // Se ejecuta al restaurar una sesión guardada.
  // Comprueba el perfil y carga los datos necesarios para mostrar la aplicación.
  const expiresAt = Number(sessionStorage.getItem(apiClient.SESSION_EXPIRY_KEY));
  if (!Number.isFinite(expiresAt) || expiresAt <= Date.now()) {
    throw new Error("La sesión venció. Inicia sesión otra vez.");
  }
  if (!user || !Number.isInteger(user.user_id) || !Array.isArray(user.roles)
      || !user.roles.some((role) => ["PASSENGER", "DRIVER"].includes(role))) {
    throw new Error("La cuenta no tiene un rol habilitado para usar QrPass.");
  }
  authenticatedUser = user;
  const pageProfile = document.body.dataset.profilePage;
  if (pageProfile !== "pasajero" && pageProfile !== "conductor") {
    throw new Error("La página no tiene un perfil de trabajo válido.");
  }
  if (!hasProfileRole(pageProfile)) {
    sessionStorage.setItem(
      "qrpass-active-profile-v1",
      hasProfileRole("conductor") ? "conductor" : "pasajero",
    );
    window.location.replace("./index.html");
    return;
  }
  currentProfile = pageProfile;
  sessionExpiryTimer = window.setTimeout(() => {
    logout("expired");
  }, expiresAt - Date.now());
  const [routes, fares] = await Promise.all([
    apiRequest("/routes"),
    apiRequest("/fares/current"),
  ]);
  routeCatalog = routes;
  // Se conserva la lista completa: incluye las tarifas por destino (ruta 48).
  fareCatalog = fares;
  const ordinaryFare = fares.find((fare) => !fare.destination);
  currentFare = ordinaryFare?.amount ?? 0;
  currentDayType = ordinaryFare?.day_type ?? "weekday";
  await refreshPassengerData();
  driverState = { activeShift: null, completedShifts: [] };

  if (currentProfile === "conductor") {
    // El rol habilita el espacio; la asignación indica si hay un turno que
    // iniciar. La autorización de cada operación sigue estando en el servidor.
    try {
      await refreshDriverAssignments();
    } catch (error) {
      if (error.status !== 404) throw error;
      driverAssignment = null;
      driverAssignments = [];
    }
    try {
      await refreshDriverShift();
    } catch (error) {
      if (error.status !== 404) throw error;
      driverState.activeShift = null;
      activeBusQr = null;
    }
    await syncServerTime();
    if (driverClockTimer) window.clearInterval(driverClockTimer);
    driverClockTimer = window.setInterval(() => syncServerTime(), 60000);
    await refreshDriverShiftHistory();
    startBusQrAutoRefresh();
  }

  document.body.classList.add("is-authenticated");
  document.querySelector(".app-shell").hidden = false;
  currentView = "inicio";
  activeFilter = "todos";
  renderCurrentView();
}

function logout(reason = "") {
  // Cerrar sesión también limpia lo que quedó en pantalla; otra persona que
  // use este dispositivo no debería heredar el saldo ni los datos anteriores.
  stopQrCamera();
  stopBusQrAutoRefresh();
  if (sessionExpiryTimer !== null) window.clearTimeout(sessionExpiryTimer);
  sessionExpiryTimer = null;
  authenticatedUser = null;
  currentProfile = "pasajero";
  driverAssignment = null;
  driverAssignments = [];
  selectedDriverRouteId = null;
  routeCatalog = [];
  state = { balance: 0, trips: [], payments: [] };
  driverState = { activeShift: null, completedShifts: [] };
  sessionStorage.removeItem(apiClient.ACCESS_TOKEN_KEY);
  sessionStorage.removeItem(apiClient.SESSION_EXPIRY_KEY);
  sessionStorage.removeItem("qrpass-active-profile-v1");
  window.location.replace(reason ? `./login.html?reason=${encodeURIComponent(reason)}` : "./login.html");
}

async function bootstrapAuthentication() {
  // Al abrir la página se intenta restaurar la sesión guardada en esta pestaña.
  const token = sessionStorage.getItem(apiClient.ACCESS_TOKEN_KEY);
  if (!token) {
    window.location.replace("./login.html");
    return;
  }
  try {
    const user = await apiRequest("/auth/me");
    await activateSession(user);
  } catch (error) {
    sessionStorage.setItem("qrpass-login-message-v1", error.message);
    logout("invalid-session");
  }
}

let state = { balance: 0, trips: [], payments: [] };

let driverState = { activeShift: null, completedShifts: [] };

// Formato de fechas y piezas pequeñas que se repiten en las pantallas.
function icon(name, className = "icon") {
  return `<svg class="${className}" aria-hidden="true"><use href="#icon-${name}"></use></svg>`;
}

function formatDate(date = new Date()) {
  return new Intl.DateTimeFormat("es-CO", { day: "2-digit", month: "short", year: "numeric", timeZone: APP_TIME_ZONE }).format(date);
}

function formatTime(date = new Date()) {
  return new Intl.DateTimeFormat("es-CO", { hour: "2-digit", minute: "2-digit", hour12: true, timeZone: APP_TIME_ZONE }).format(date);
}

function currentDateLong(date = new Date()) {
  return new Intl.DateTimeFormat("es-CO", { weekday: "long", day: "numeric", month: "long", timeZone: APP_TIME_ZONE }).format(date);
}

function pageHeading(eyebrow, title, description, action = "") {
  return `<div class="page-heading">
    <div><div class="eyebrow">${eyebrow}</div><h1>${title}</h1>${description ? `<p>${description}</p>` : ""}</div>
    ${action}
  </div>`;
}

function emptyTrips(message, columns = 5) {
  return `<tr><td class="empty-row" colspan="${columns}">${message}</td></tr>`;
}

function tripRow(trip) {
  const route = escapeHtml(trip.route);
  const method = escapeHtml(trip.method);
  return `<tr>
    <td class="trip-route"><span class="route-token">${route.slice(0, 2)}</span>Ruta ${route}</td>
    <td>${escapeHtml(formatDate(new Date(trip.createdAt)))}</td>
    <td><span class="payment-tag">${method}</span></td>
    <td>${trip.amount === 0 ? "Sin costo" : money(trip.amount)}</td>
    <td><span class="status-pill">Registrado</span></td>
  </tr>`;
}

function pageTable(trips, className = "") {
  return `<div class="surface">
    <div class="surface-header"><div><h2>Actividad reciente</h2></div></div>
    <div class="table-wrap"><table class="trip-table ${className}">
      <thead><tr><th>Ruta</th><th>Fecha</th><th>Medio de pago</th><th>Valor</th><th>Estado</th></tr></thead>
      <tbody>${trips.length ? trips.map(tripRow).join("") : emptyTrips("Cuando pagues tu primer viaje, aparecerá aquí.")}</tbody>
    </table></div>
  </div>`;
}

// Pantallas del pasajero: resumen, actividad y accesos rápidos.
function getRecentTrips() {
  return [...state.trips].reverse().slice(0, 4);
}

function renderDashboard() {
  const fare = getFare();
  const tripCount = state.trips.length;
  const lastTrip = state.trips.at(-1);
  const lastMethod = lastTrip?.method ?? "—";
  const lastTripNote = lastTrip
    ? `Último viaje: ${formatDate(new Date(lastTrip.createdAt))}`
    : "Sin viajes todavía";
  const lastMethodNote = lastTrip?.route
    ? `Ruta ${escapeHtml(lastTrip.route)}`
    : "Tu actividad aparecerá aquí";
  return `${pageHeading(
    `<span class="eyebrow-dot"></span> RESUMEN DE TU CUENTA`,
    `Hola, ${escapeHtml(authenticatedUser.names)}`,
    "",
    `<span class="heading-date">${currentDateLong()}</span>`,
  )}
  <section class="welcome-banner">
    <div class="welcome-copy">
      <div class="eyebrow">${icon("qr")} PAGO DEL PASAJE</div>
      <h2>Paga aquí.</h2>
      <p>El valor se descuenta de tu saldo.</p>
      <button class="button button-mint" data-action="pay-qr">Escanear QR del bus ${icon("arrow")}</button>
    </div>
    <div class="welcome-illustration" aria-hidden="true">
      ${icon("bus")}
    </div>
  </section>
  <section class="stats-grid" aria-label="Estadísticas de tu cuenta">
    <article class="stat-card"><div class="stat-top"><span class="stat-label">SALDO DISPONIBLE</span><span class="stat-icon">${icon("wallet")}</span></div><div class="stat-value">${money(state.balance)}</div><div class="stat-note">${state.balance > 0 ? "Disponible para viajar" : "Recarga para viajar"}</div></article>
    <article class="stat-card"><div class="stat-top"><span class="stat-label">TARIFA VIGENTE</span><span class="stat-icon amber">${icon("route")}</span></div><div class="stat-value">${money(fare)}</div><div class="stat-note">${currentDayType === "weekend" ? "Domingos y festivos" : "Lunes a sábado"} · por viaje</div></article>
    <article class="stat-card"><div class="stat-top"><span class="stat-label">VIAJES REGISTRADOS</span><span class="stat-icon green">${icon("bus")}</span></div><div class="stat-value">${tripCount}</div><div class="stat-note">${lastTripNote}</div></article>
    <article class="stat-card"><div class="stat-top"><span class="stat-label">ÚLTIMO MÉTODO</span><span class="stat-icon dark">${icon("clock")}</span></div><div class="stat-value stat-value-method">${escapeHtml(lastMethod)}</div><div class="stat-note">${lastMethodNote}</div></article>
  </section>
  <section class="content-grid">
    <div>${pageTable(getRecentTrips())}</div>
    <div class="side-stack">
      <article class="quick-card"><h2 class="quick-card-heading">Acciones rápidas</h2><div class="quick-actions">
        <button class="quick-action" data-action="pay-qr">${icon("qr")}<span>Pagar con saldo</span>${icon("arrow", "icon quick-arrow")}</button>
        <button class="quick-action" data-action="payment" data-method="efectivo">${icon("bus")}<span>Pago en efectivo</span>${icon("arrow", "icon quick-arrow")}</button>
        <button class="quick-action" data-action="quick-top-up">${icon("plus")}<span>Recargar saldo</span>${icon("arrow", "icon quick-arrow")}</button>
      </div></article>
    </div>
  </section>`;
}

// Pantalla del conductor y controles de su turno.
function renderDriverDashboard() {
  const shift = driverState.activeShift;
  const latestShift = driverState.completedShifts.at(-1);
  const heading = pageHeading(
    `${icon("bus")} OPERACIÓN DE TRANSPORTE`,
    "Mi turno y pagos",
    "Muestra el QR a los pasajeros, registra los pagos en efectivo o tarjeta y revisa el total al terminar.",
  );

  if (!shift) {
    activeBusQr = null;
    const latestSummary = latestShift
      ? `<article class="shift-summary-card${latestShift.cashDifference ? " has-difference" : ""}">
          <div class="shift-summary-heading">${icon(latestShift.cashDifference ? "clock" : "check")}<strong>Último turno</strong></div>
          <div class="shift-summary-grid"><span>${escapeHtml(formatDate(new Date(latestShift.startedAt)))}</span><span>${latestShift.entries.length} ${latestShift.entries.length === 1 ? "pago" : "pagos"}</span><span>Total recibido ${money(latestShift.total)}</span></div>
          <p>${latestShift.cashDifference ? `Diferencia de efectivo: ${money(Math.abs(latestShift.cashDifference))} ${latestShift.cashDifference > 0 ? "de más" : "faltante"} (contaste ${money(latestShift.cashCounted)} · registraste ${money(latestShift.cashExpected)}).` : "El efectivo contado coincide con los pagos registrados."}</p>
        </article>`
      : "";
    return `${heading}
      <section class="driver-shift-hero">
        <div class="driver-shift-copy"><div class="eyebrow">${icon("clock")} ASIGNACIÓN OPERATIVA</div>
          <h2>No hay un turno activo</h2><p>${driverAssignment ? "Revisa la ruta y el vehículo asignados. Al iniciar el turno podrás mostrar el QR y registrar los pagos recibidos." : "No tienes una ruta asignada por ahora. Puedes consultar los turnos anteriores o pedir una asignación al administrador."}</p>
        </div>
        <div class="assigned-shift"><span>RUTA ASIGNADA</span><strong>Ruta ${escapeHtml(driverAssignment?.route_name ?? "—")} <i>·</i> Vehículo ${escapeHtml(driverAssignment?.vehicle_plate ?? "—")}</strong><small>Conductor ${escapeHtml(driverAssignment?.driver_name ?? authenticatedUser.names)}</small></div>
        ${driverAssignments.length > 1 ? `<div class="form-field section-gap"><label for="driver-route-select">Ruta a iniciar</label><select class="select" id="driver-route-select">${driverAssignments.map((item) => `<option value="${item.route_id}"${item.route_id === selectedDriverRouteId ? " selected" : ""}>Ruta ${escapeHtml(item.route_name)} · ${escapeHtml(item.vehicle_plate)}</option>`).join("")}</select></div>` : ""}
        <button class="button button-mint" type="button" data-action="start-driver-shift"${driverAssignment ? "" : " disabled"}>${icon("check")} ${driverAssignment ? "Iniciar turno" : "No hay ruta asignada"}</button>
      </section>
      ${latestSummary}`;
  }

  const entries = shift.entries;
  const cashTotal = entries.filter((entry) => entry.method === "Efectivo").reduce((total, entry) => total + entry.amount, 0);
  const walletTotal = entries.filter((entry) => entry.method === "QR / saldo").reduce((total, entry) => total + entry.amount, 0);
  const cardTotal = entries.filter((entry) => entry.method === "Tarjeta").reduce((total, entry) => total + entry.amount, 0);
  const total = cashTotal + walletTotal + cardTotal;
  const rows = [...entries].reverse().slice(0, 8).map((entry) => `<tr>
    <td><span class="driver-ledger-code">${escapeHtml(entry.reference)}</span></td>
    <td>${escapeHtml(formatTime(new Date(entry.createdAt)))}</td>
    <td><span class="payment-tag">${escapeHtml(entry.method)}</span></td>
    <td>${money(entry.amount)}</td>
  </tr>`).join("");

  return `${heading}
    <section class="active-shift-banner">
      <div class="active-shift-status"><span class="active-shift-pulse"></span> TURNO ACTIVO</div>
      <h2>Ruta ${escapeHtml(shift.route)} <span>·</span> Vehículo ${escapeHtml(shift.vehicle)}</h2>
      <p>Inicio registrado ${escapeHtml(formatTime(new Date(shift.startedAt)))} · <span id="driver-boardings-count">${entries.length} ${entries.length === 1 ? "abordaje" : "abordajes"} en esta jornada</span></p>
      <div class="active-shift-reference">Número de turno: ${escapeHtml(shift.reference)}</div>
    </section>
    <section class="surface detail-card bus-qr-card">
      <h2>QR para pagar el pasaje</h2>
      <p>Muestra este código a los pasajeros para que lo escaneen con su celular. Se actualiza solo cada 60 segundos y apenas un pasajero lo usa.</p>
      <div id="bus-qr-live">${renderBusQrBlock(shift)}</div>
      <button class="button button-outline" type="button" data-action="refresh-bus-qr">Crear un nuevo código</button>
      <div class="driver-live-payments" id="driver-live-payments">${renderDriverLivePayments(entries)}</div>
    </section>
    <section class="driver-totals" aria-label="Pagos registrados en el turno">
      <article><span>EFECTIVO</span><strong id="driver-total-cash">${money(cashTotal)}</strong><small id="driver-count-cash">${entries.filter((entry) => entry.method === "Efectivo").length} registros</small></article>
      <article><span>PAGOS CON QR / SALDO</span><strong id="driver-total-wallet">${money(walletTotal)}</strong><small id="driver-count-wallet">${entries.filter((entry) => entry.method === "QR / saldo").length} registros</small></article>
      <article><span>TARJETA</span><strong id="driver-total-card">${money(cardTotal)}</strong><small id="driver-count-card">${entries.filter((entry) => entry.method === "Tarjeta").length} registros</small></article>
      <article class="driver-total-all"><span>TOTAL DE PAGOS</span><strong id="driver-total-all">${money(total)}</strong><small id="driver-count-all">${entries.length} ${entries.length === 1 ? "pago registrado" : "pagos registrados"}</small></article>
    </section>
    <section class="driver-work-grid">
      <article class="driver-capture-card">
        <div class="eyebrow">${icon("plus")} REGISTRO DE PAGO · TURNO ACTIVO</div>
        <h2>¿Cómo pagó el pasajero?</h2>
        <div class="driver-payment-actions">
          <button type="button" data-action="driver-payment" data-method="cash">${icon("wallet")}<span><strong>Efectivo</strong><small>Recibido en la unidad</small></span>${icon("arrow")}</button>
          <button type="button" data-action="driver-payment" data-method="card">${icon("card")}<span><strong>Tarjeta</strong><small>Solo queda anotado</small></span>${icon("arrow")}</button>
        </div>
      </article>
      <article class="driver-close-card">
        <div class="eyebrow">${icon("check")} TERMINAR TURNO</div><h2>Revisa el efectivo recibido</h2>
        <p>Cuenta el efectivo y compáralo con los <strong id="driver-cash-expected">${money(cashTotal)}</strong> registrados.</p>
        <form id="close-driver-shift-form">
          <label for="driver-cash-counted">¿Cuánto efectivo tienes? (COP)</label>
          <input class="input" id="driver-cash-counted" name="cashCounted" type="number" inputmode="numeric" min="0" step="1" value="${cashTotal}" required />
          <button class="button button-outline" type="submit">Terminar turno</button>
        </form>
        <small>Al terminar el turno, ya no podrás registrar más pagos. El resumen mostrará si el efectivo coincide.</small>
      </article>
    </section>
    <section class="surface driver-ledger">
      <div class="surface-header"><div><h2>Pagos registrados</h2><p id="driver-ledger-count">${entries.length} ${entries.length === 1 ? "pago" : "pagos"} en este turno</p></div></div>
      <div class="table-wrap"><table class="trip-table driver-ledger-table">
        <thead><tr><th>Número</th><th>Hora</th><th>Medio de pago</th><th>Valor</th></tr></thead>
        <tbody id="driver-ledger-body">${rows || `<tr><td class="empty-row" colspan="4">Aún no hay pagos registrados. Al anotarlos, aparecerán aquí.</td></tr>`}</tbody>
      </table></div>
    </section>
    <article class="driver-integrity-note">${icon("shield")}<div><strong>Registro de pagos</strong><p>Los pagos con QR descuentan el saldo del pasajero en su billetera QrPass. El efectivo y la tarjeta se anotan para el control del turno.</p></div></article>`;
}

function finderCell(row, column, top, left) {
  const y = row - top;
  const x = column - left;
  if (x < 0 || x > 6 || y < 0 || y > 6) return null;
  return x === 0 || x === 6 || y === 0 || y === 6 || (x >= 2 && x <= 4 && y >= 2 && y <= 4);
}

function qrCells(seed) {
  let hash = 0;
  for (const character of seed) hash = (hash * 31 + character.charCodeAt(0)) >>> 0;
  let cells = "";
  for (let row = 0; row < 21; row += 1) {
    for (let column = 0; column < 21; column += 1) {
      const finder = finderCell(row, column, 0, 0)
        ?? finderCell(row, column, 0, 14)
        ?? finderCell(row, column, 14, 0);
      hash = (hash * 1664525 + 1013904223) >>> 0;
      const dark = finder ?? ((hash >>> 29) & 1) === 1;
      cells += `<span class="qr-cell${dark ? " is-dark" : ""}"></span>`;
    }
  }
  return cells;
}

function renderQr() {
  return `${pageHeading(`${icon("qr")} TU VIAJE`, "Escanear QR del bus", "Apunta la cámara al código del bus o escríbelo a mano.")}
    <article class="surface detail-card qr-generation-card">
      <p>El pasaje cuesta <strong>${money(getFare())}</strong> y se descuenta de tu saldo al confirmar.</p>
      <form id="passenger-qr-form" data-idempotency-key="${createIdempotencyKey()}">
        <div class="form-field"><label for="passenger-qr-token">Código QR del bus</label><input class="input" id="passenger-qr-token" name="token" type="text" minlength="20" maxlength="512" autocomplete="off" autocapitalize="off" spellcheck="false" required /></div>
        <video id="passenger-qr-video" class="qr-camera-preview" playsinline muted hidden></video>
        <div class="modal-actions"><button class="button button-outline" type="button" data-action="scan-passenger-camera">Abrir cámara</button><button class="button" type="submit">Pagar pasaje</button></div>
      </form>
    </article>`;
}

function renderTopUp() {
  const amounts = [10000, 20000, 50000, 100000];
  return `${pageHeading(`${icon("wallet")} TU BILLETERA`, "Recarga tu saldo")}
  <section class="balance-banner"><div><div class="eyebrow">SALDO ACTUAL</div><h2>${money(state.balance)}</h2></div>${icon("wallet")}</section>
  <section class="surface detail-card"><h2>Elige el monto</h2><div class="amount-grid">${amounts.map((amount) => `<button class="amount-option" data-action="top-up" data-amount="${amount}"><strong>${money(amount)}</strong></button>`).join("")}</div>
  <form class="custom-amount" id="custom-top-up"><label for="custom-amount">Otro monto (máximo ${money(500000)})</label><input class="input" id="custom-amount" name="amount" type="number" inputmode="numeric" min="1" max="500000" step="1" placeholder="Ej. 35.000" required /><button class="button" type="submit">${icon("plus")} Recargar</button></form></section>`;
}

function renderHistory() {
  const allMovements = state.payments
    .map((payment) => {
      const trip = state.trips.find((item) => item.tripId === payment.tripId);
      return { ...payment, transferDestination: trip?.transferredTo ?? null };
    })
    .sort((first, second) => new Date(second.createdAt) - new Date(first.createdAt));
  const matches = allMovements.filter((movement) => {
    if (activeFilter === "todos") return true;
    if (activeFilter === "recargas") return movement.type === "top_up";
    if (activeFilter === "traspasos") return Boolean(movement.transferDestination);
    if (activeFilter === "saldo") return movement.method === "Saldo QR";
    if (activeFilter === "efectivo") return movement.method === "Efectivo";
    if (activeFilter === "tarjeta") return movement.method.startsWith("Tarjeta");
    return true;
  });
  const fareTotal = matches
    .filter((movement) => movement.type === "fare_payment")
    .reduce((sum, movement) => sum + movement.amount, 0);
  const rows = matches.map((movement) => {
    const route = movement.route ? `Ruta ${escapeHtml(movement.route)}` : "&mdash;";
    const title = movement.type === "top_up" ? "Recarga"
      : movement.transferDestination ? "Pasaje transbordado"
      : "Pasaje";
    return `<tr>
      <td class="trip-route"><span class="route-token">${escapeHtml(title.slice(0, 2))}</span>${title}</td>
      <td>${escapeHtml(formatDate(new Date(movement.createdAt)))} &middot; ${escapeHtml(formatTime(new Date(movement.createdAt)))}</td>
      <td><span class="payment-tag">${escapeHtml(movement.method)}</span></td>
      <td>${route}</td>
      <td>${movement.amount ? money(movement.amount) : "Sin costo"}</td>
      <td><button class="text-link" type="button" data-action="payment-detail" data-payment-id="${escapeHtml(movement.id)}">Ver detalle ${icon("arrow")}</button></td>
    </tr>`;
  });

  return `${pageHeading(`${icon("clock")} TU ACTIVIDAD`, "Movimientos", "Pagos, recargas y traspasos de tu cuenta.")}
  <div class="history-summary">
    <div><span>Movimientos</span><br /><strong>${matches.length}</strong></div>
    <div><span>Pasajes pagados</span><br /><strong>${money(fareTotal)}</strong></div>
    <label class="sr-only" for="history-filter">Filtrar movimientos</label>
    <select class="select filter-select" id="history-filter">
      <option value="todos" ${activeFilter === "todos" ? "selected" : ""}>Todos los movimientos</option>
      <option value="recargas" ${activeFilter === "recargas" ? "selected" : ""}>Recargas</option>
      <option value="saldo" ${activeFilter === "saldo" ? "selected" : ""}>Saldo QR</option>
      <option value="efectivo" ${activeFilter === "efectivo" ? "selected" : ""}>Efectivo</option>
      <option value="tarjeta" ${activeFilter === "tarjeta" ? "selected" : ""}>Tarjeta</option>
      <option value="traspasos" ${activeFilter === "traspasos" ? "selected" : ""}>Traspasos</option>
    </select>
  </div>
  <div class="surface"><div class="surface-header"><div><h2>Detalle de movimientos</h2></div></div>
    <div class="table-wrap"><table class="trip-table history-table">
      <thead><tr><th>Tipo</th><th>Fecha y hora</th><th>Medio</th><th>Ruta</th><th>Valor</th><th>Detalle</th></tr></thead>
      <tbody>${rows.length ? rows.join("") : emptyTrips("No hay movimientos con este filtro.", 6)}</tbody>
    </table></div>
  </div>`;
}

const VIEW_LABELS = { inicio: "Resumen", qr: "Escanear QR del bus", historial: "Mis viajes", recarga: "Recargar saldo" };

// Elegimos la pantalla actual y dejamos la navegación al día.
function renderCurrentView() {
  // Esta función central decide qué contenido va dentro del área principal.
  // Los datos se preparan en otras funciones; aquí solo se elige y dibuja la vista.
  if (!authenticatedUser || !hasProfileRole(currentProfile)) return;
  const views = { inicio: renderDashboard, qr: renderQr, historial: renderHistory, recarga: renderTopUp };
  const renderer = currentProfile === "conductor"
    ? renderDriverDashboard
    : views[currentView] ?? views.inicio;
  content.innerHTML = renderer();
  document.querySelector("#page-crumb").textContent = currentProfile === "conductor"
    ? "Mi turno"
    : VIEW_LABELS[currentView] ?? VIEW_LABELS.inicio;
  document.querySelectorAll(".nav-link[data-view]").forEach((link) => {
    link.classList.toggle("is-active", link.dataset.view === currentView);
    if (link.dataset.view === currentView) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
  document.querySelectorAll(".mobile-tab[data-tab-view]").forEach((link) => {
    link.hidden = currentProfile === "conductor";
    link.classList.toggle("is-active", link.dataset.tabView === currentView);
    if (link.dataset.tabView === currentView) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
  document.querySelectorAll("[data-profile-content]").forEach((section) => {
    section.hidden = section.dataset.profileContent !== currentProfile;
  });
  document.querySelector("#mobile-tabbar").hidden = currentProfile === "conductor";
  document.querySelectorAll(".profile-switcher [data-profile]").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.profile === currentProfile));
  });
  const hasMultipleRoles = hasProfileRole("pasajero") && hasProfileRole("conductor");
  const initials = authenticatedUser.names.split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase();
  document.querySelector("#workspace-switcher").hidden = !hasMultipleRoles;
  document.querySelector("#sidebar-avatar").textContent = initials;
  document.querySelector("#topbar-avatar").textContent = initials;
  document.querySelector("#sidebar-name").textContent = authenticatedUser.names;
  document.querySelector("#sidebar-role").textContent = `${currentProfile === "conductor" ? "Espacio conductor" : "Espacio pasajero"}`;
  document.querySelector("#breadcrumb-context").textContent = currentProfile === "conductor"
    ? "Conductor"
    : "Pasajero";
  document.querySelector("#today-date").textContent = currentDateLong();
}

// Cambios de perfil, turno y menú de navegación.
async function setProfile(profile) {
  // Cambia entre los espacios que el usuario realmente puede usar.
  // Si entra al conductor, primero vuelve a pedir sus datos al servidor.
  stopQrCamera();
  if ((profile !== "pasajero" && profile !== "conductor") || !hasProfileRole(profile)) {
    showToast("Tu cuenta no tiene autorización para ese espacio.", true);
    renderCurrentView();
    return;
  }
  if (profile !== currentProfile) {
    // Persistimos el rol para que la página de entrada restaure la selección correcta.
    try {
      sessionStorage.setItem("qrpass-active-profile-v1", profile);
    } catch (error) {
      console.error("No se pudo guardar el espacio seleccionado:", error);
      showToast("No se pudo guardar el espacio en esta sesión.", true);
      return;
    }
    window.location.replace(profile === "conductor" ? "./conductor.html" : "./pasajero.html");
    return;
  }
  if (profile === "conductor") {
    try {
      try {
        await refreshDriverAssignments();
      } catch (error) {
        if (error.status !== 404) throw error;
        driverAssignment = null;
        driverAssignments = [];
      }
      try {
        await refreshDriverShift();
      } catch (error) {
        if (error.status !== 404) throw error;
        driverState.activeShift = null;
        activeBusQr = null;
      }
      await refreshDriverShiftHistory();
    } catch (error) {
      showToast(error.message, true);
      if (error.status === 401 || error.status === 403) logout();
      return;
    }
  }
  currentProfile = profile;
  currentView = "inicio";
  try {
    sessionStorage.setItem("qrpass-active-profile-v1", currentProfile);
  } catch (error) {
    console.error("No se pudo guardar el espacio seleccionado:", error);
    showToast("No se pudo guardar el espacio en esta sesión.", true);
  }
  renderCurrentView();
  setMenuOpen(false);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function startDriverShift() {
  // La interfaz solicita iniciar el turno asignado; el backend valida la ruta
  // y decide si el cambio de estado está permitido.
  if (!driverAssignment && !driverAssignments.length) {
    showToast("No hay una asignación disponible para iniciar.", true);
    return;
  }
  const routeSelect = document.querySelector("#driver-route-select");
  if (routeSelect) selectedDriverRouteId = Number(routeSelect.value);
  const routeId = selectedDriverRouteId ?? driverAssignment?.route_id;
  if (!routeId) {
    showToast("Selecciona una ruta asignada para iniciar.", true);
    return;
  }
  try {
    await apiRequest(`/driver/shift/start?route_id=${routeId}`, { method: "POST" });
    await refreshDriverShift();
    renderCurrentView();
    showToast("Turno iniciado.");
  } catch (error) {
    showToast(error.message, true);
    if (error.status === 401) logout();
  }
}

async function recordDriverPayment(method, cardType = null, idempotencyKey = createIdempotencyKey()) {
  // Registra los pagos en efectivo o tarjeta recibidos durante el turno.
  if (!["cash", "card"].includes(method) || (method === "card" && !["debit", "credit"].includes(cardType))) {
    showToast("Selecciona un medio de pago válido.", true);
    return;
  }
  try {
    const result = await apiRequest("/driver/shift/payments", {
      method: "POST",
      body: JSON.stringify({
        method,
        ...(cardType ? { card_type: cardType } : {}),
        idempotency_key: idempotencyKey,
      }),
    });
    await refreshDriverShift();
    renderCurrentView();
    showToast(`${result.method === "cash" ? "Efectivo" : "Tarjeta"} registrado en el turno.`);
    return true;
  } catch (error) {
    showToast(error.message, true);
    if (error.status === 401) logout();
    return false;
  }
}

let jsQrLoader = null;

// Carga jsQR solo cuando hace falta (navegadores sin BarcodeDetector, como Safari en iPhone).
function loadJsQr() {
  if (window.jsQR) return Promise.resolve(window.jsQR);
  if (!jsQrLoader) {
    jsQrLoader = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = "./jsQR.js";
      script.onload = () => resolve(window.jsQR);
      script.onerror = () => {
        jsQrLoader = null;
        reject(new Error("No se pudo cargar el lector QR."));
      };
      document.head.append(script);
    });
  }
  return jsQrLoader;
}

// Devuelve una función que lee un cuadro del video y entrega el texto del QR (o null).
async function createQrReader(video) {
  if ("BarcodeDetector" in window) {
    const detector = new BarcodeDetector({ formats: ["qr_code"] });
    return async () => {
      const codes = await detector.detect(video);
      return codes.length ? codes[0].rawValue : null;
    };
  }
  const jsQR = await loadJsQr();
  const canvas = document.createElement("canvas");
  const context = canvas.getContext("2d", { willReadFrequently: true });
  return async () => {
    if (!video.videoWidth || !video.videoHeight) return null;
    const scale = Math.min(1, 800 / video.videoWidth);
    canvas.width = Math.round(video.videoWidth * scale);
    canvas.height = Math.round(video.videoHeight * scale);
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    const image = context.getImageData(0, 0, canvas.width, canvas.height);
    const result = jsQR(image.data, image.width, image.height, { inversionAttempts: "dontInvert" });
    return result ? result.data : null;
  };
}

async function startQrCamera(formId, inputId, videoId) {
  // La cámara captura el código; el servidor sigue siendo quien lo valida.
  if (!navigator.mediaDevices?.getUserMedia) {
    showToast("Este navegador o esta conexión no permite abrir la cámara (requiere HTTPS). Escribe o pega el código del bus.", true);
    return;
  }
  try {
    activeCameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
    const video = document.querySelector(`#${videoId}`);
    video.srcObject = activeCameraStream;
    video.hidden = false;
    await video.play();
    const readQr = await createQrReader(video);
    const scan = async () => {
      if (!video.isConnected || !activeCameraStream) return;
      try {
        const value = await readQr();
        if (value) {
          document.querySelector(`#${inputId}`).value = value;
          stopQrCamera();
          document.querySelector(`#${formId}`).requestSubmit();
          return;
        }
      } catch (error) {
        console.error("Error leyendo un cuadro de la cámara:", error);
      }
      scanLoopTimer = window.setTimeout(scan, 200);
    };
    await scan();
  } catch (error) {
    stopQrCamera();
    console.error("No se pudo iniciar el lector QR:", error);
    showToast("No se pudo abrir la cámara. Revisa el permiso del navegador o escribe el código del bus.", true);
  }
}

function stopQrCamera() {
  if (scanLoopTimer !== null) window.clearTimeout(scanLoopTimer);
  scanLoopTimer = null;
  activeCameraStream?.getTracks().forEach((track) => track.stop());
  activeCameraStream = null;
}

async function closeDriverShift(cashCounted) {
  // Envía el efectivo contado para que el servidor cierre y calcule la diferencia.
  const shift = driverState.activeShift;
  if (!shift) {
    showToast("No hay un turno activo para cerrar.", true);
    return;
  }
  if (!Number.isSafeInteger(cashCounted) || cashCounted < 0) {
    showToast("Ingresa un valor entero de efectivo igual o mayor que cero.", true);
    return;
  }
  try {
    const report = await apiRequest("/driver/shift/close", {
      method: "POST",
      body: JSON.stringify({ cash_counted: cashCounted }),
    });
    const closed = report.shift;
    const cashDifference = closed.cash_difference ?? 0;
    // Una vez cerrado, el servidor es quien impide agregar movimientos a ese
    // turno; aquí quitamos la vista activa y dejamos el resumen en el historial.
    driverState.completedShifts.unshift(mapShiftFromApi(closed));
    driverState.activeShift = null;
    driverPaymentsSignature = "";
    activeBusQr = null;
    // Conserva la asignación para que el conductor pueda iniciar un nuevo turno
    // sin recargar la página ni depender de un administrador.
    try {
      await refreshDriverAssignments();
    } catch (error) {
      if (error.status !== 404) throw error;
      driverAssignment = null;
      driverAssignments = [];
    }
    renderCurrentView();
    openShiftReceipt(closed);
    showToast(cashDifference
      ? `Cierre guardado. Diferencia de efectivo: ${money(Math.abs(cashDifference))} ${cashDifference > 0 ? "de más" : "faltante"}.`
      : "Turno terminado. El efectivo contado coincide con los pagos registrados.");
  } catch (error) {
    showToast(error.message, true);
    if (error.status === 401) logout();
  }
}

function openShiftReceipt(shift) {
  const total = shift.cash_total + shift.qr_total + shift.card_total;
  const difference = shift.cash_difference ?? 0;
  modalContent.innerHTML = `<div class="modal-body">
    <div class="receipt-mark">${icon("check")}</div>
    <div class="modal-kicker">RESUMEN DEL TURNO</div>
    <h2 id="modal-title">Turno terminado</h2>
    <p>Este turno ya está cerrado. Aquí tienes el resumen de los pagos.</p>
    <div class="receipt-list">
      <div class="detail-row"><span>Referencia del turno</span><strong>${escapeHtml(`TUR-${shift.shift_id}`)}</strong></div>
      <div class="detail-row"><span>Ruta</span><strong>${escapeHtml(shift.route_name)}</strong></div>
      <div class="detail-row"><span>Pasajes registrados</span><strong>${shift.payment_count}</strong></div>
      <div class="detail-row"><span>QR / saldo</span><strong>${money(shift.qr_total)}</strong></div>
      <div class="detail-row"><span>Efectivo anotado</span><strong>${money(shift.cash_total)}</strong></div>
      <div class="detail-row"><span>Recaudo con tarjeta</span><strong>${money(shift.card_total)}</strong></div>
      <div class="detail-row"><span>Total recaudado</span><strong>${money(total)}</strong></div>
      <div class="detail-row"><span>Efectivo contado</span><strong>${money(shift.cash_counted)}</strong></div>
      <div class="detail-row"><span>Diferencia de caja</span><strong>${difference ? money(Math.abs(difference)) : "Cuadra"}</strong></div>
    </div>
    <div class="modal-actions"><button class="button" type="button" data-action="close-modal">Entendido</button></div>
  </div>`;
  modal.showModal();
}

function setMenuOpen(isOpen) {
  sidebar.classList.toggle("is-open", isOpen);
  sidebarBackdrop.classList.toggle("is-visible", isOpen);
  const menuToggle = document.querySelector("#menu-toggle");
  menuToggle.setAttribute("aria-expanded", String(isOpen));
  menuToggle.setAttribute("aria-label", isOpen ? "Cerrar menú" : "Abrir menú");
  document.body.classList.toggle("menu-open", isOpen);
}

function navigateTo(view) {
  if (!(view in VIEW_LABELS)) return;
  stopQrCamera();
  currentView = view;
  renderCurrentView();
  setMenuOpen(false);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function updateConnectionStatus() {
  const offline = !navigator.onLine;
  connectionStatus.classList.toggle("is-offline", offline);
  connectionLabel.textContent = offline ? "Sin conexión · interfaz" : "Conectado";
}

function updateInstallButton() {
  const isStandalone = window.matchMedia("(display-mode: standalone)").matches
    || window.navigator.standalone === true;
  installButton.hidden = isStandalone || (!deferredInstallPrompt && window.innerWidth > 760);
}

// Diálogos, avisos y acciones que acompañan el recorrido.
function openPlatformInfo() {
  const canViewMetrics = authenticatedUser?.roles.includes("ADMIN") ?? false;
  modal.classList.add("platform-info-open");
  modalContent.innerHTML = `<article class="platform-info-container">
    <header class="platform-info-header">
      <span class="platform-info-title">${icon("document")}<span id="modal-title">Sobre la plataforma</span></span>
      <button class="icon-button platform-info-close" type="button" data-action="close-modal" aria-label="Cerrar información">${icon("close")}</button>
    </header>
    <section class="platform-info-body">
      <span class="platform-info-intro">QrPass conecta tu billetera con el transporte público de Ibagué.</span>
      <p>Puedes usar las funciones de pasajero y, si tu cuenta tiene permiso, también las de conductor. Si tienes ambos permisos, puedes cambiar de espacio desde la parte superior.</p>
      <h3>Qué puedes hacer</h3>
      <ul><li>Como pasajero: escanear el QR del bus, pagar con tu saldo, consultar tus viajes y solicitar un cambio de ruta cuando esté permitido.</li><li>Como conductor: iniciar la ruta asignada, mostrar el QR, anotar pagos y terminar el turno contando el efectivo.</li></ul>
      <h3>Alcance del servicio</h3>
      <ul><li>Para pagar con QR se necesita conexión a internet.</li><li>Las rutas, tarifas y reglas se administran desde el catálogo de la plataforma.</li></ul>
      <h3>Acerca de tus datos</h3>
      <p>No ingreses datos bancarios ni compartas tu contraseña.</p>
      ${canViewMetrics ? `<button class="button button-outline" type="button" data-action="view-global-metrics"><svg class="icon"><use href="#icon-grid"></use></svg> Ver resumen general</button>` : ""}
    </section>
    <footer class="platform-info-footer"><span>Ventana informativa. Cerrarla no realiza ninguna transacción.</span><button class="button" type="button" data-action="close-modal">Entendido</button></footer>
  </article>`;
  modal.showModal();
}


async function openGlobalMetrics() {
  modal.classList.remove("platform-info-open");
  try {
    const metrics = await apiRequest("/admin/metrics");
    modalContent.innerHTML = `<div class="modal-body">
      <div class="modal-kicker">CONSOLIDADO · GERENCIA DE TRANSPORTE</div>
      <h2 id="modal-title">Métricas Globales de Recaudo</h2>
      <div class="receipt-list">
        <div class="receipt-row"><span>Total recaudado</span><strong>${money(metrics.total_collected)}</strong></div>
        <div class="receipt-row"><span>Recaudo en efectivo</span><span>${money(metrics.cash_collected)}</span></div>
        <div class="receipt-row"><span>Recaudo código QR</span><span>${money(metrics.qr_collected)}</span></div>
        <div class="receipt-row"><span>Recaudo con tarjeta</span><span>${money(metrics.card_collected)}</span></div>
        <div class="receipt-row"><span>Total de viajes</span><span>${metrics.total_trips}</span></div>
        <div class="receipt-row"><span>Transbordos ($0 COP)</span><span>${metrics.total_transfers} transbordos</span></div>
        <div class="receipt-row"><span>Turnos activos de bus</span><span>${metrics.active_shifts} en servicio</span></div>
        <div class="receipt-row"><span>Rutas habilitadas</span><span>${metrics.total_routes} rutas</span></div>
        <div class="receipt-row"><span>Usuarios en el sistema</span><span>${metrics.total_users} usuarios</span></div>
      </div>
      <div class="modal-actions" style="margin-top: 1.5rem;">
        <button class="button" type="button" data-action="close-modal">Cerrar</button>
      </div>
    </div>`;
    modal.showModal();
  } catch (error) {
    showToast(error.message, "error");
  }
}

function openPrivacyInfo() {
  modal.classList.remove("platform-info-open");
  modalContent.innerHTML = `<div class="modal-body">
    <div class="modal-kicker">DATOS</div>
    <h2 id="modal-title">Aviso de privacidad</h2>
    <p>Este aviso explica cómo QrPass usa los datos de tu cuenta.</p>
    <div class="receipt-list">
      <div class="detail-row"><span>Datos de registro</span><strong>Nombre, correo y contraseña</strong></div>
      <div class="detail-row"><span>Datos de uso</span><strong>Saldo, pagos y viajes</strong></div>
      <div class="detail-row"><span>Para qué se usan</span><strong>Acceso a la cuenta y operación de los viajes</strong></div>
      <div class="detail-row"><span>Almacenamiento</span><strong>Base de datos de QrPass</strong></div>
    </div>
    <p>La contraseña se guarda como un hash seguro. No escribas datos bancarios ni uses una contraseña que tengas en otros servicios. Para ejercer tus derechos sobre los datos, contacta al administrador de la plataforma.</p>
    <div class="modal-actions"><button class="button" type="button" data-action="close-modal">Cerrar aviso</button></div>
  </div>`;
  modal.showModal();
}

async function installApp() {
  if (!deferredInstallPrompt) {
    modalContent.innerHTML = `<div class="modal-body"><div class="modal-kicker">INSTALACIÓN</div><h2 id="modal-title">Añade QrPass a tu pantalla de inicio</h2><p>Al instalarla podrás abrir la plataforma desde un icono, como una app.</p>
      <div class="receipt-list"><div class="detail-row"><span>En iPhone o iPad</span><strong>Safari → Compartir → Añadir a pantalla de inicio</strong></div><div class="detail-row"><span>En Android</span><strong>Chrome → ⋮ → Instalar aplicación o Añadir a pantalla de inicio</strong></div></div>
      <div class="validity-row">${icon("shield")}<span>Abre QrPass desde una dirección segura (HTTPS) o desde localhost. Abrir el archivo directamente no permite instalarla ni activar el modo sin conexión.</span></div>
      <div class="modal-actions"><button class="button" data-action="close-modal">Entendido</button></div></div>`;
    modal.showModal();
    return;
  }

  deferredInstallPrompt.prompt();
  const { outcome } = await deferredInstallPrompt.userChoice;
  deferredInstallPrompt = null;
  updateInstallButton();
  if (outcome === "accepted") showToast("QrPass se está instalando en tu dispositivo.");
}

function showToast(message, isError = false) {
  const toast = document.createElement("div");
  toast.className = `toast${isError ? " is-error" : ""}`;
  toast.innerHTML = `${icon(isError ? "clock" : "check")}<span>${escapeHtml(message)}</span>`;
  toastRegion.append(toast);
  window.setTimeout(() => toast.remove(), 3600);
}

function openReceipt(trip, isTransfer = false) {
  // El recibo resume el movimiento confirmado por el servidor.
  modalContent.innerHTML = `<div class="modal-body">
    <div class="receipt-mark">${icon("check")}</div><div class="modal-kicker">COMPROBANTE</div>
    <h2 id="modal-title">${isTransfer ? "Tu pago fue transferido" : trip.movementType === "top_up" ? "Recarga registrada" : "Pago registrado"}</h2>
    <div class="receipt-list">
      <div class="detail-row"><span>Ruta</span><strong>${escapeHtml(trip.route)}</strong></div>
      <div class="detail-row"><span>Método</span><strong>${escapeHtml(trip.method)}</strong></div>
      <div class="detail-row"><span>Valor</span><strong>${trip.amount ? money(trip.amount) : "Sin costo adicional"}</strong></div>
      <div class="detail-row"><span>Referencia</span><strong>${escapeHtml(trip.code)}</strong></div>
      <div class="detail-row"><span>Fecha y hora</span><strong>${escapeHtml(formatDate(new Date(trip.createdAt)))} · ${escapeHtml(formatTime(new Date(trip.createdAt)))}</strong></div>
    </div>
    <div class="modal-actions"><button class="button" data-action="close-modal">Entendido</button></div>
  </div>`;
  if (!modal.open) modal.showModal();
}

function openMovementDetails(movementId) {
  const payment = state.payments.find((item) => item.id === movementId);
  const trip = state.trips.find((item) => item.tripId === payment?.tripId);
  const movement = payment
    ? { ...payment, transferDestination: trip?.transferredTo ?? null }
    : null;
  if (!movement) {
    showToast("No encontramos el detalle de ese movimiento.", true);
    return;
  }

  const isTopUp = movement.type === "top_up";
  const kind = isTopUp ? "Recarga" : "Pago de pasaje";
  const amountLabel = isTopUp ? "Valor recargado" : "Valor del movimiento";
  const balanceRows = movement.balanceBefore === undefined ? "" : `
    <div class="detail-row"><span>Saldo anterior</span><strong>${money(movement.balanceBefore)}</strong></div>
    <div class="detail-row"><span>Saldo posterior</span><strong>${money(movement.balanceAfter)}</strong></div>`;
  const routeRows = movement.route ? `
    <div class="detail-row"><span>Ruta</span><strong>${escapeHtml(movement.route)}</strong></div>` : "";
  const transferRows = movement.transferDestination ? `
    <div class="detail-row"><span>Transbordo a</span><strong>${escapeHtml(movement.transferDestination)}</strong></div>
    <div class="detail-row"><span>Tarifa adicional</span><strong>Sin costo</strong></div>` : "";

  modalContent.innerHTML = `<div class="modal-body">
    <div class="receipt-mark">${icon("document")}</div>
    <div class="modal-kicker">DETALLE DE MOVIMIENTO</div>
    <h2 id="modal-title">${kind}</h2>
    <p>Este registro es informativo y no sustituye un comprobante financiero oficial.</p>
    <div class="receipt-list">
      <div class="detail-row"><span>Referencia</span><strong>${escapeHtml(movement.reference)}</strong></div>
      <div class="detail-row"><span>M&eacute;todo</span><strong>${escapeHtml(movement.method)}</strong></div>
      ${routeRows}${transferRows}
      <div class="detail-row"><span>${amountLabel}</span><strong>${movement.amount ? money(movement.amount) : "Sin costo"}</strong></div>
      ${balanceRows}
      <div class="detail-row"><span>Estado</span><strong>${escapeHtml(movement.status)}</strong></div>
      <div class="detail-row"><span>Fecha y hora</span><strong>${escapeHtml(formatDate(new Date(movement.createdAt)))} &middot; ${escapeHtml(formatTime(new Date(movement.createdAt)))}</strong></div>
    </div>
    <div class="modal-actions"><button class="button" type="button" data-action="close-modal">Cerrar</button></div>
  </div>`;
  modal.showModal();
}

function routeOptions(excludedRoute = "") {
  return routeCatalog
    .filter((route) => route.name !== excludedRoute)
    .map((route) => `<option value="${route.id}">Ruta ${escapeHtml(route.name)}</option>`).join("");
}

function openPayment(method = "saldo") {
  // El saldo se paga escaneando el QR del bus, no escogiendo una ruta a mano.
  if (method === "saldo") {
    modal.close();
    navigateTo("qr");
    return;
  }
  selectedPaymentMethod = method;
  const fare = getFare();
  const cardTypeField = method === "tarjeta"
    ? `<div class="form-field"><label for="card-type">Tipo de tarjeta</label><select class="select" id="card-type" name="cardType" required><option value="" disabled selected>Selecciona una opción</option><option value="Débito">Débito</option><option value="Crédito">Crédito</option></select></div>`
    : "";
  const paymentMethods = [
    { value: "efectivo", label: "Efectivo", detail: "Pagas al abordar", icon: "bus" },
    { value: "tarjeta", label: "Tarjeta", detail: "Débito o crédito", icon: "card" },
  ];
  modalContent.innerHTML = `<div class="modal-body">
    <div class="modal-kicker">PAGO DE PASAJE</div><h2 id="modal-title">Registra tu viaje</h2>
    <form id="payment-form" data-idempotency-key="${createIdempotencyKey()}">
      <div class="payment-route-row" id="payment-route-row">
        <div class="form-field"><label for="payment-route">Ruta que vas a abordar</label><select class="select" id="payment-route" name="route" required><option value="" disabled selected>Selecciona una ruta</option>${routeOptions()}</select></div>
        <div class="form-field" id="payment-destination-field"></div>
      </div>
      <fieldset class="payment-fieldset"><legend>Método de pago</legend>
        <div class="method-picker">${paymentMethods.map((option) => `<label class="method-choice">
          <input class="method-radio" type="radio" name="method" value="${option.value}"${method === option.value ? " checked" : ""} />
          <span class="method-tile"><span class="method-radio-indicator"></span>${icon(option.icon, "icon method-icon")}<span class="method-label">${option.label}</span><span class="method-detail">${option.detail}</span></span>
        </label>`).join("")}</div>
      </fieldset>
      <div id="card-type-container">${cardTypeField}</div>
      <div class="modal-total"><span>Valor del pasaje</span><strong id="payment-total">${money(fare)}</strong></div>
      <div class="modal-actions"><button class="button button-outline" type="button" data-action="close-modal">Cancelar</button><button class="button" type="submit">Confirmar movimiento</button></div>
    </form>
  </div>`;
  modal.showModal();
}

function choosePaymentMethod(method) {
  const route = document.querySelector("#payment-route")?.value ?? "";
  const destination = document.querySelector("#payment-destination")?.value ?? "";
  openPayment(method);
  const routeInput = document.querySelector("#payment-route");
  if (route && routeInput) {
    routeInput.value = route;
    renderPaymentDestination(destination);
  }
}

// Muestra el menú "Destino" al lado de la ruta solo cuando la ruta elegida
// tiene destinos (hoy, la 48); en las demás rutas el menú no aparece.
function renderPaymentDestination(selectedDestination = "") {
  const row = document.querySelector("#payment-route-row");
  const field = document.querySelector("#payment-destination-field");
  if (!row || !field) return;
  const routeId = Number(document.querySelector("#payment-route")?.value);
  const destinations = routeDestinations(routeId);
  row.classList.toggle("has-destination", destinations.length > 0);
  field.innerHTML = destinations.length
    ? `<label for="payment-destination">Destino</label><select class="select" id="payment-destination" name="destination" required><option value="" disabled selected>Selecciona un destino</option>${destinations.map((name) => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`).join("")}</select>`
    : "";
  if (selectedDestination && destinations.includes(selectedDestination)) {
    field.querySelector("select").value = selectedDestination;
  }
  updatePaymentTotal();
}

// El valor mostrado cambia con la ruta y el destino elegidos.
function updatePaymentTotal() {
  const total = document.querySelector("#payment-total");
  if (!total) return;
  const routeId = Number(document.querySelector("#payment-route")?.value);
  const destination = document.querySelector("#payment-destination")?.value ?? "";
  total.textContent = routeDestinations(routeId).length && !destination
    ? "Elige un destino"
    : money(getFareFor(routeId, destination));
}

function updatePaymentMethod(method) {
  if (!["efectivo", "tarjeta"].includes(method)) return;
  selectedPaymentMethod = method;
  const cardTypeContainer = document.querySelector("#card-type-container");
  const totalLabel = document.querySelector(".modal-total span");

  cardTypeContainer.innerHTML = method === "tarjeta"
    ? `<div class="form-field"><label for="card-type">Tipo de tarjeta</label><select class="select" id="card-type" name="cardType" required><option value="" disabled selected>Selecciona una opción</option><option value="Débito">Débito</option><option value="Crédito">Crédito</option></select></div>`
    : "";
  totalLabel.textContent = "Valor del pasaje";
}

function openTransfer() {
  const latestPaidTrip = [...state.trips].reverse().find((trip) => trip.amount > 0 && !trip.transferred && trip.tripId);
  if (!latestPaidTrip) {
    modalContent.innerHTML = `<div class="modal-body"><div class="modal-kicker">CAMBIO DE RUTA</div><h2 id="modal-title">Aún no hay un pago para transferir</h2><p>Primero escanea el QR del bus para registrar el viaje. Después podrás solicitar el transbordo.</p><div class="modal-actions"><button class="button button-outline" data-action="close-modal">Cerrar</button><button class="button" data-action="payment" data-method="saldo">Escanear QR del bus</button></div></div>`;
    modal.showModal();
    return;
  }
  modalContent.innerHTML = `<div class="modal-body"><div class="modal-kicker">CAMBIO DE RUTA</div><h2 id="modal-title">Transfiere tu pago</h2><p>Si abordaste el bus equivocado, indica la ruta correcta dentro de los 20 minutos. El pago original no se vuelve a cobrar.</p>
    <form id="transfer-form" data-trip-id="${latestPaidTrip.tripId}">
      <div class="validity-row">${icon("arrows")}<span>Pago ${escapeHtml(latestPaidTrip.code)} · Ruta ${escapeHtml(latestPaidTrip.route)} · ${money(latestPaidTrip.amount)}</span></div>
      <div class="form-field section-gap"><label for="transfer-route">Ruta correcta</label><select class="select" id="transfer-route" name="route" required><option value="" disabled selected>Selecciona otra ruta</option>${routeOptions(latestPaidTrip.route)}</select></div>
      <div class="modal-total"><span>Costo adicional</span><strong>${money(0)}</strong></div>
      <div class="modal-actions"><button class="button button-outline" type="button" data-action="close-modal">Cancelar</button><button class="button" type="submit">Confirmar traspaso</button></div>
    </form>
  </div>`;
  modal.showModal();
}

function openQuickTopUp() {
  const amounts = [10000, 20000, 50000, 100000];
  modalContent.innerHTML = `<div class="modal-body">
    <div class="modal-kicker">BILLETERA</div><h2 id="modal-title">Añadir saldo</h2>
    <p>Se abona de inmediato.</p>
    <div class="amount-grid">${amounts.map((amount) => `<button class="amount-option" data-action="top-up" data-amount="${amount}"><strong>${money(amount)}</strong></button>`).join("")}</div>
    <div class="modal-actions"><button class="button button-outline" type="button" data-action="view-recarga">Escribir otro monto</button><button class="button button-outline" type="button" data-action="close-modal">Cerrar</button></div>
  </div>`;
  if (!modal.open) modal.showModal();
}

async function topUp(amount, trigger) {
  if (!Number.isInteger(amount) || amount < 1 || amount > 500000) {
    showToast("El monto debe estar entre $1 y $500.000.", true);
    return;
  }
  if (trigger) trigger.disabled = true;
  const idempotencyKey = trigger?.dataset.idempotencyKey ?? createIdempotencyKey();
  if (trigger) trigger.dataset.idempotencyKey = idempotencyKey;
  try {
    const receipt = await apiRequest("/account/top-ups", {
      method: "POST",
      body: JSON.stringify({ amount, idempotency_key: idempotencyKey }),
    });
    if (trigger) delete trigger.dataset.idempotencyKey;
    await refreshPassengerData();
    renderCurrentView();
    openReceipt({
      route: "Billetera",
      method: "Recarga",
      movementType: "top_up",
      amount: receipt.amount,
      code: `REC-${receipt.payment_id}`,
      createdAt: receipt.created_at,
    });
  } catch (error) {
    showToast(error.message, true);
    if (error.status === 401) logout();
  } finally {
    if (trigger?.isConnected) trigger.disabled = false;
  }
}

// Conectamos los controles una sola vez, incluso los que aparecen después.
document.addEventListener("click", async (event) => {
  // La mayoría de las pantallas se vuelve a dibujar; escuchar en el documento
  // permite que los botones recién creados sigan respondiendo.
  // Los botones de las pantallas se crean al dibujarlas; este listener único
  // sigue funcionando aunque el HTML interno se reemplace.
  const target = event.target.closest("[data-profile], [data-view], [data-action]");
  if (!target) return;

  if (target.dataset.profile) {
    setProfile(target.dataset.profile);
    return;
  }
  if (target.dataset.view) {
    navigateTo(target.dataset.view);
    return;
  }

  const { action, method, amount } = target.dataset;
  if (action === "payment") openPayment(method || "saldo");
  if (action === "pay-qr") {
    navigateTo("qr");
    startQrCamera("passenger-qr-form", "passenger-qr-token", "passenger-qr-video");
  }
  if (action === "quick-top-up") openQuickTopUp();
  if (action === "view-recarga") {
    modal.close();
    navigateTo("recarga");
  }
  if (action === "transfer") openTransfer();
  if (action === "platform-info") openPlatformInfo();
  if (action === "privacy-info") openPrivacyInfo();
  if (action === "view-global-metrics") openGlobalMetrics();
  if (action === "logout") logout();
  if (action === "start-driver-shift") startDriverShift();
  if (action === "refresh-bus-qr") {
    try {
      const qr = await apiRequest("/driver/shift/qr?renew=true", { method: "POST" });
      activeBusQr = { image: qr.image_data_uri, expiresAt: new Date(qr.expires_at), token: qr.token };
      renderCurrentView();
      showToast("QR del bus actualizado.");
    } catch (error) {
      showToast(error.message, true);
    }
  }
  if (action === "copy-qr-token") {
    const tokenField = document.querySelector(".qr-token-full");
    if (!activeBusQr?.token || !tokenField) {
      showToast("El código QR no está disponible.", true);
    } else {
      let copied = false;
      try {
        if (navigator.clipboard?.writeText) {
          await navigator.clipboard.writeText(activeBusQr.token);
          copied = true;
        }
      } catch {
        // HTTP on a local network is not a secure context for the Clipboard API.
      }
      if (!copied) {
        tokenField.focus();
        tokenField.select();
        try {
          copied = document.execCommand("copy");
        } catch {
          // Keep the full token selected so it can still be copied manually.
        }
      }
      if (copied) {
        showToast("Código copiado. Ya puedes compartirlo con el pasajero.");
      } else {
        tokenField.focus();
        tokenField.select();
        showToast("No se pudo copiar. El código quedó seleccionado; toca Copiar en tu dispositivo.", true);
      }
    }
  }
  if (action === "driver-payment") {
    if (method === "card") {
      openDriverCardPayment();
    } else {
      const idempotencyKey = target.dataset.idempotencyKey ?? createIdempotencyKey();
      target.dataset.idempotencyKey = idempotencyKey;
      target.disabled = true;
      const recorded = await recordDriverPayment(method, null, idempotencyKey);
      if (recorded) delete target.dataset.idempotencyKey;
      if (target.isConnected) target.disabled = false;
    }
  }
  if (action === "choose-method") choosePaymentMethod(method);
  if (action === "scan-passenger-camera") {
    startQrCamera("passenger-qr-form", "passenger-qr-token", "passenger-qr-video");
  }
  if (action === "close-modal") modal.close();
  if (action === "payment-detail") openMovementDetails(target.dataset.paymentId);
  if (action === "top-up") topUp(Number(amount), target);
});

function openDriverCardPayment() {
  modalContent.innerHTML = `<div class="modal-body">
    <div class="modal-kicker">TARJETA</div><h2 id="modal-title">Anota el pago con tarjeta</h2>
    <form id="driver-card-payment-form" data-idempotency-key="${createIdempotencyKey()}">
      <div class="form-field"><label for="driver-card-type">Tipo de tarjeta</label><select class="select" id="driver-card-type" name="cardType" required><option value="" disabled selected>Selecciona una opción</option><option value="debit">Débito</option><option value="credit">Crédito</option></select></div>
      <div class="modal-actions"><button class="button button-outline" type="button" data-action="close-modal">Cancelar</button><button class="button" type="submit">Guardar registro</button></div>
    </form>
  </div>`;
  modal.showModal();
}

document.addEventListener("input", (event) => {
  // Si el conductor escribe el efectivo contado, las actualizaciones automáticas ya no lo sobrescriben.
  if (event.target.id === "driver-cash-counted") event.target.dataset.touched = "true";
});

document.addEventListener("submit", async (event) => {
  // Los formularios de las ventanas aparecen y desaparecen según el recorrido;
  // una sola entrada mantiene parecida la respuesta aunque cambie el contenido.
  if (event.target.id === "passenger-qr-form") {
    event.preventDefault();
    const form = event.target;
    const submit = form.querySelector('button[type="submit"]');
    submit.disabled = true;
    try {
      // La clave se conserva durante el envío para impedir cobros duplicados.
      const result = await apiRequest("/account/qr/validate", {
        method: "POST",
        body: JSON.stringify({
          token: new FormData(form).get("token"),
          idempotency_key: form.dataset.idempotencyKey,
        }),
      });
      await refreshPassengerData();
      renderCurrentView();
      openReceipt({
        route: result.route_name,
        method: "Saldo QR",
        amount: result.amount,
        code: `VIA-${result.trip_id}`,
        createdAt: result.created_at,
      });
    } catch (error) {
      showToast(error.message, true);
      if (error.status === 401) logout();
    } finally {
      submit.disabled = false;
    }
  }

  if (event.target.id === "driver-card-payment-form") {
    event.preventDefault();
    const form = event.target;
    const cardType = new FormData(form).get("cardType");
    const submit = form.querySelector('button[type="submit"]');
    submit.disabled = true;
    const recorded = await recordDriverPayment("card", cardType, form.dataset.idempotencyKey);
    if (recorded) modal.close();
    else if (form.isConnected) submit.disabled = false;
  }

  if (event.target.id === "close-driver-shift-form") {
    event.preventDefault();
    await closeDriverShift(Number(new FormData(event.target).get("cashCounted")));
  }

  if (event.target.id === "payment-form") {
    event.preventDefault();
    const formData = new FormData(event.target);
    const routeId = Number(formData.get("route"));
    const route = routeCatalog.find((item) => item.id === routeId)?.name;
    selectedPaymentMethod = String(formData.get("method") ?? "");
    // Estas comprobaciones dan respuesta rápida en la pantalla. El backend
    // vuelve a comprobarlas porque es quien protege los datos y las reglas.
    if (!route) {
      showToast("Selecciona una ruta disponible.", true);
      return;
    }
    const destination = String(formData.get("destination") ?? "");
    if (routeDestinations(routeId).length && !destination) {
      showToast("Selecciona un destino para esta ruta.", true);
      return;
    }
    const cardType = formData.get("cardType");
    if (selectedPaymentMethod === "tarjeta" && !["Débito", "Crédito"].includes(cardType)) {
      showToast("Selecciona débito o crédito.", true);
      return;
    }
    const paymentMethods = { efectivo: "cash", tarjeta: "card" };
    const cardTypes = { Débito: "debit", Crédito: "credit" };
    const submit = event.target.querySelector('button[type="submit"]');
    submit.disabled = true;
    try {
      // Si hay un corte justo después de confirmar, el mismo formulario guarda
      // la misma clave para que el reintento no cree un segundo movimiento.
      const receipt = await apiRequest("/account/payments", {
        method: "POST",
        body: JSON.stringify({
          route_id: routeId,
          ...(destination ? { destination } : {}),
          method: paymentMethods[selectedPaymentMethod],
          ...(selectedPaymentMethod === "tarjeta" ? { card_type: cardTypes[cardType] } : {}),
          idempotency_key: event.target.dataset.idempotencyKey,
        }),
      });
      const trip = {
        route: receipt.destination ? `${receipt.route_name} · ${receipt.destination}` : receipt.route_name,
        method: receipt.method === "wallet" ? "Saldo QR"
          : receipt.method === "cash" ? "Efectivo"
          : `Tarjeta ${receipt.card_type === "credit" ? "crédito" : "débito"}`,
        amount: receipt.amount,
        code: `PAGO-${receipt.payment_id}`,
        tripId: receipt.trip_id,
        createdAt: receipt.created_at,
      };
      modal.close();
      await refreshPassengerData();
      renderCurrentView();
      openReceipt(trip);
    } catch (error) {
      showToast(error.message, true);
      if (error.status === 401) logout();
    } finally {
      submit.disabled = false;
    }
  }

  if (event.target.id === "transfer-form") {
    event.preventDefault();
    const destinationRouteId = Number(new FormData(event.target).get("route"));
    const source = state.trips.find((trip) => trip.tripId === Number(event.target.dataset.tripId));
    // Se comprueba que el viaje y el destino estén en pantalla; el servicio
    // también valida propiedad, tiempo y ruta antes de guardar el traspaso.
    if (!source || !routeCatalog.some((route) => route.id === destinationRouteId) || source.transferred) {
      showToast("No se pudo validar el pago y la nueva ruta.", true);
      return;
    }
    try {
      const transfer = await apiRequest("/account/transfers", {
        method: "POST",
        body: JSON.stringify({ trip_id: source.tripId, destination_route_id: destinationRouteId }),
      });
      const trip = {
        route: transfer.destination_route,
        method: `Traspaso desde ${transfer.origin_route}`,
        amount: 0,
        code: `TRASP-${transfer.transfer_id}`,
        createdAt: transfer.created_at,
      };
      modal.close();
      await refreshPassengerData();
      renderCurrentView();
      openReceipt(trip, true);
    } catch (error) {
      showToast(error.message, true);
      if (error.status === 401) logout();
    }
  }

  if (event.target.id === "custom-top-up") {
    event.preventDefault();
    const amount = Number(new FormData(event.target).get("amount"));
    if (!Number.isInteger(amount) || amount < 1 || amount > 500000) {
      showToast("Ingresa un monto entero entre $1 y $500.000.", true);
      return;
    }
    await topUp(amount, event.target.querySelector('button[type="submit"]'));
  }
});

document.addEventListener("change", (event) => {
  if (event.target.id === "history-filter") {
    activeFilter = event.target.value;
    renderCurrentView();
  }
  if (event.target.name === "method" && event.target.form?.id === "payment-form") {
    updatePaymentMethod(event.target.value);
  }
  if (event.target.id === "payment-route") renderPaymentDestination();
  if (event.target.id === "payment-destination") updatePaymentTotal();
});

document.querySelector("#menu-toggle").addEventListener("click", (event) => {
  setMenuOpen(!sidebar.classList.contains("is-open"));
});

sidebarBackdrop.addEventListener("click", () => setMenuOpen(false));

document.addEventListener("click", (event) => {
  if (window.innerWidth <= 760 && sidebar.classList.contains("is-open")
      && !sidebar.contains(event.target) && !event.target.closest("#menu-toggle")) {
    setMenuOpen(false);
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && sidebar.classList.contains("is-open")) setMenuOpen(false);
});

installButton.addEventListener("click", installApp);

// Al volver a la pestaña (por ejemplo, tras desbloquear el celular) se pide enseguida el QR vigente.
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) syncBusQr();
});

modal.addEventListener("close", () => {
  modal.classList.remove("platform-info-open");
  stopQrCamera();
});

modal.addEventListener("click", (event) => {
  if (event.target === modal) modal.close();
});

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  deferredInstallPrompt = event;
  updateInstallButton();
});

window.addEventListener("appinstalled", () => {
  deferredInstallPrompt = null;
  updateInstallButton();
  showToast("QrPass quedó instalada en tu dispositivo.");
});

window.addEventListener("online", updateConnectionStatus);
window.addEventListener("offline", updateConnectionStatus);
window.addEventListener("resize", updateInstallButton);

document.querySelector("#today-date").textContent = currentDateLong();
updateConnectionStatus();
updateInstallButton();
bootstrapAuthentication();

if ("serviceWorker" in navigator && window.isSecureContext) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("./cache.js")
      .then(() => console.info("QrPass: soporte de plataforma sin conexión activado."))
      .catch((error) => {
        console.error("No se pudo registrar el modo sin conexión de QrPass:", error);
        showToast("No se pudo activar el modo sin conexión en este navegador.", true);
      });
  });
}
