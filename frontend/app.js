// La pantalla sigue el recorrido de la persona; el servidor conserva las
// decisiones y el historial. Si algo cambia dinero o un viaje, se confirma allí.
// Arrancamos con lo que la interfaz necesita y guardamos aquí su estado.
const ACCESS_TOKEN_KEY = "qrpass-access-token-v1";
const SESSION_EXPIRY_KEY = "qrpass-session-expiry-v1";
const API_BASE_URL = globalThis.QRPASS_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

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
let accessToken = null;
let sessionExpiryTimer = null;
let activeFilter = "todos";
let activeBusQr = null;
let selectedPaymentMethod = "saldo";
let deferredInstallPrompt = null;
let routeCatalog = [];
let currentFare = 3300;
let driverAssignment = null;
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

function hasProfileRole(profile) {
  if (profile !== "pasajero" && profile !== "conductor") return false;
  const role = profile === "conductor" ? "DRIVER" : "PASSENGER";
  return authenticatedUser?.roles.includes(role) ?? false;
}

async function apiRequest(path, options = {}) {
  // Todas las pantallas hablan con la API por aquí para que una caída de red
  // o un rechazo se convierta en un mensaje entendible, no en una pantalla rota.
  // Se centralizan encabezados y token para que cada pantalla no repita el login.
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");
  if (options.body) headers.set("Content-Type", "application/json");
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  } catch (error) {
    throw new Error("No se pudo conectar con QrPass. Comprueba que la API esté iniciada.");
  }

  // La interfaz espera JSON tanto en respuestas exitosas como en errores.
  let payload;
  try {
    payload = await response.json();
  } catch (error) {
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
    status: payment.status === "completed_demo" ? "Registrado en demo" : payment.status,
    createdAt: payment.created_at,
    reference: `PAGO-${payment.payment_id}`,
  };
}

async function refreshPassengerData() {
  // Al volver de una operación, reconstruimos saldo e historial desde el
  // servidor: la memoria de esta pestaña no es el registro oficial.
  // Saldo e historial se piden en paralelo para que la pantalla muestre datos actuales.
  const [account, trips, history] = await Promise.all([
    apiRequest("/demo/account"),
    apiRequest("/demo/account/trips"),
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
  const qr = await apiRequest("/driver/shift/qr", { method: "POST" });
  activeBusQr = { image: qr.image_data_uri, expiresAt: new Date(qr.expires_at) };
}

async function refreshDriverShiftHistory() {
  const shifts = await apiRequest("/driver/shifts/history");
  driverState.completedShifts = shifts.map(mapShiftFromApi);
}

function showLoginError(message = "") {
  const error = document.querySelector("#login-error");
  error.textContent = message;
  error.hidden = !message;
}

async function activateSession(user, token) {
  // Se ejecuta después del login y al restaurar una sesión guardada.
  // Comprueba el perfil y carga los datos necesarios para mostrar la aplicación.
  const expiresAt = Number(sessionStorage.getItem(SESSION_EXPIRY_KEY));
  if (!Number.isFinite(expiresAt) || expiresAt <= Date.now()) {
    throw new Error("La sesión venció. Inicia sesión otra vez.");
  }
  if (!user || !Number.isInteger(user.user_id) || !Array.isArray(user.roles)
      || !user.roles.some((role) => ["PASSENGER", "DRIVER"].includes(role))) {
    throw new Error("La cuenta no tiene un rol habilitado para usar QrPass.");
  }
  authenticatedUser = user;
  accessToken = token;
  sessionExpiryTimer = window.setTimeout(() => {
    logout();
    showLoginError("La sesión venció. Inicia sesión otra vez.");
  }, expiresAt - Date.now());
  const [routes, fares] = await Promise.all([
    apiRequest("/routes"),
    apiRequest("/fares/current"),
  ]);
  routeCatalog = routes;
  currentFare = fares[0]?.amount ?? 3300;
  await refreshPassengerData();
  driverState = { activeShift: null, completedShifts: [] };
  const preferredProfile = sessionStorage.getItem("qrpass-active-profile-v1");
  currentProfile = preferredProfile && hasProfileRole(preferredProfile)
    ? preferredProfile
    : hasProfileRole("conductor") ? "conductor" : "pasajero";

  if (currentProfile === "conductor") {
    // El rol habilita el espacio; la asignación indica si hay un turno que
    // iniciar. La autorización de cada operación sigue estando en el servidor.
    try {
      driverAssignment = await apiRequest("/driver/demo/assignment");
    } catch (error) {
      if (error.status !== 404) throw error;
      driverAssignment = null;
    }
    try {
      await refreshDriverShift();
    } catch (error) {
      if (error.status !== 404) throw error;
      driverState.activeShift = null;
      activeBusQr = null;
    }
    await refreshDriverShiftHistory();
  }

  document.body.classList.add("is-authenticated");
  document.querySelector("#login-gate").hidden = true;
  document.querySelector(".app-shell").hidden = false;
  currentView = "inicio";
  activeFilter = "todos";
  renderCurrentView();
}

function logout() {
  // Cerrar sesión también limpia lo que quedó en pantalla; otra persona que
  // use este dispositivo no debería heredar el saldo ni los datos anteriores.
  stopQrCamera();
  if (sessionExpiryTimer !== null) window.clearTimeout(sessionExpiryTimer);
  sessionExpiryTimer = null;
  accessToken = null;
  authenticatedUser = null;
  currentProfile = "pasajero";
  driverAssignment = null;
  activeBusQr = null;
  routeCatalog = [];
  state = { balance: 0, trips: [], payments: [] };
  driverState = { activeShift: null, completedShifts: [] };
  sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  sessionStorage.removeItem(SESSION_EXPIRY_KEY);
  sessionStorage.removeItem("qrpass-active-profile-v1");
  document.body.classList.remove("is-authenticated");
  document.querySelector("#login-gate").hidden = false;
  document.querySelector(".app-shell").hidden = true;
  document.querySelector("#login-form").reset();
  document.querySelector("#registration-form").reset();
  document.querySelector("#login-form").hidden = false;
  document.querySelector("#registration-form").hidden = true;
  document.querySelector("#registration-toggle").textContent = "Crear cuenta de pasajero";
  document.querySelector("#registration-toggle").hidden = false;
  document.querySelector("#registration-error").hidden = true;
  showLoginError();
  setMenuOpen(false);
  modal.close();
}

async function bootstrapAuthentication() {
  // Al abrir la página se intenta restaurar la sesión guardada en esta pestaña.
  const token = sessionStorage.getItem(ACCESS_TOKEN_KEY);
  if (!token) return;
  accessToken = token;
  try {
    const user = await apiRequest("/auth/me");
    await activateSession(user, token);
  } catch (error) {
    logout();
    showLoginError(error.message);
  }
}

let state = { balance: 0, trips: [], payments: [] };

let driverState = { activeShift: null, completedShifts: [] };

// Formato de fechas y piezas pequeñas que se repiten en las pantallas.
function icon(name, className = "icon") {
  return `<svg class="${className}" aria-hidden="true"><use href="#icon-${name}"></use></svg>`;
}

function formatDate(date = new Date()) {
  return new Intl.DateTimeFormat("es-CO", { day: "2-digit", month: "short", year: "numeric" }).format(date);
}

function formatTime(date = new Date()) {
  return new Intl.DateTimeFormat("es-CO", { hour: "2-digit", minute: "2-digit", hour12: true }).format(date);
}

function currentDateLong(date = new Date()) {
  return new Intl.DateTimeFormat("es-CO", { weekday: "long", day: "numeric", month: "long" }).format(date);
}

function pageHeading(eyebrow, title, description, action = "") {
  return `<div class="page-heading">
    <div><div class="eyebrow">${eyebrow}</div><h1>${title}</h1><p>${description}</p></div>
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
    <div class="surface-header"><div><h2>Actividad reciente</h2><p>El detalle de tus últimos viajes</p></div></div>
    <div class="table-wrap"><table class="trip-table ${className}">
      <thead><tr><th>Ruta</th><th>Fecha</th><th>Medio de pago</th><th>Valor</th><th>Estado</th></tr></thead>
      <tbody>${trips.length ? trips.map(tripRow).join("") : emptyTrips("Aún no hay viajes. Tu primera salida está a un clic.")}</tbody>
    </table></div>
  </div>`;
}

// Pantallas del pasajero: resumen, actividad y accesos rápidos.
function getRecentTrips() {
  return [...state.trips].reverse().slice(0, 4);
}

function getWeeklyActivity() {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const days = Array.from({ length: 7 }, (_, index) => {
    const day = new Date(today);
    day.setDate(today.getDate() - (6 - index));
    return { date: day, amount: 0, trips: 0 };
  });

  for (const trip of state.trips) {
    const tripDate = new Date(trip.createdAt);
    if (Number.isNaN(tripDate.getTime())) continue;
    tripDate.setHours(0, 0, 0, 0);
    const index = days.findIndex((day) => day.date.getTime() === tripDate.getTime());
    if (index !== -1) {
      days[index].amount += trip.amount;
      days[index].trips += 1;
    }
  }

  return days;
}

function renderWeeklyActivity() {
  const days = getWeeklyActivity();
  const totalAmount = days.reduce((sum, day) => sum + day.amount, 0);
  const totalTrips = days.reduce((sum, day) => sum + day.trips, 0);
  const maxAmount = Math.max(...days.map((day) => day.amount), 1);
  const points = days.map((day, index) => {
    const x = 12 + (index * 456) / 6;
    const y = 92 - (day.amount / maxAmount) * 64;
    return { ...day, x, y };
  });
  const linePath = points.map((point, index) =>
    `${index === 0 ? "M" : "L"} ${point.x.toFixed(1)} ${point.y.toFixed(1)}`).join(" ");
  const areaPath = `${linePath} L 468 104 L 12 104 Z`;
  const labels = points.map((point) =>
    `<span>${escapeHtml(new Intl.DateTimeFormat("es-CO", { weekday: "short" }).format(point.date).replace(".", ""))}</span>`).join("");
  const accessibleSummary = points.map((point) =>
    `${new Intl.DateTimeFormat("es-CO", { weekday: "long", day: "numeric" }).format(point.date)}: ${point.trips} viajes, ${money(point.amount)}`).join(". ");

  return `<article class="weekly-card">
    <div class="weekly-header">
      <div><div class="eyebrow">${icon("route")} TU MOVILIDAD</div><h2>Tu semana en movimiento</h2><p>Pasajes registrados en los últimos 7 días</p></div>
      <span class="weekly-demo-badge"><span></span> DEMO</span>
    </div>
    <div class="weekly-summary"><div><span>Gasto simulado</span><strong>${money(totalAmount)}</strong></div><div><span>Viajes</span><strong>${totalTrips}</strong></div></div>
    <svg class="weekly-chart" viewBox="0 0 480 116" role="img" aria-label="${escapeHtml(accessibleSummary)}" preserveAspectRatio="none">
      <defs><linearGradient id="weekly-fill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stop-color="#62b970" stop-opacity=".22"/><stop offset="100%" stop-color="#62b970" stop-opacity="0"/></linearGradient></defs>
      <path class="weekly-gridline" d="M 12 28 H 468 M 12 60 H 468 M 12 104 H 468"/>
      <path class="weekly-area" d="${areaPath}"/>
      <path class="weekly-line" d="${linePath}"/>
      ${points.map((point) => `<circle class="weekly-point${point.trips ? " has-trips" : ""}" cx="${point.x.toFixed(1)}" cy="${point.y.toFixed(1)}" r="${point.trips ? 4 : 2.5}"><title>${escapeHtml(new Intl.DateTimeFormat("es-CO", { weekday: "long", day: "numeric" }).format(point.date))}: ${point.trips} viajes, ${money(point.amount)}</title></circle>`).join("")}
    </svg>
    <div class="weekly-day-labels" aria-hidden="true">${labels}</div>
    <p class="weekly-footnote">${totalTrips ? "El resumen se calcula con los movimientos devueltos por la API de demostración." : "Cuando registres viajes, aquí verás tu actividad de la semana."}</p>
  </article>`;
}

function renderDashboard() {
  const fare = getFare();
  const tripCount = state.trips.length;
  const lastMethod = state.trips.at(-1)?.method ?? "Todavía no tienes viajes";
  return `${pageHeading(
    `<span class="eyebrow-dot"></span> TU DÍA, A TU RITMO`,
    `Hola, ${escapeHtml(authenticatedUser.names)}`,
    "Todo lo que necesitas para moverte por Ibagué, en un solo lugar.",
    `<span class="heading-date">${currentDateLong()}</span>`,
  )}
  <section class="welcome-banner">
    <button class="welcome-demo-badge" type="button" data-action="demo-info"><span></span> MODO DEMO</button>
    <div class="welcome-copy">
      <div class="eyebrow">${icon("spark")} MENOS VUELTAS, MÁS CIUDAD</div>
      <h2>Tu próximo viaje empieza aquí.</h2>
      <p>Escanea el código del bus para pagar tu abordaje.</p>
      <button class="button button-mint" data-view="qr">Escanear QR del bus ${icon("arrow")}</button>
    </div>
    <div class="welcome-orbit" aria-hidden="true"></div>
    <div class="welcome-illustration" aria-hidden="true">
      <span class="orbit-chip orbit-chip-one">${icon("qr")}</span>
      ${icon("bus")}
      <span class="orbit-chip orbit-chip-two">${icon("route")}</span>
    </div>
  </section>
  <section class="stats-grid" aria-label="Resumen de tu cuenta">
    <article class="stat-card"><div class="stat-top"><span class="stat-label">SALDO DISPONIBLE</span><span class="stat-icon">${icon("wallet")}</span></div><div class="stat-value">${money(state.balance)}</div><div class="stat-note"><span class="positive">●</span> Listo para tu próximo viaje</div></article>
    <article class="stat-card"><div class="stat-top"><span class="stat-label">TARIFA DE HOY</span><span class="stat-icon amber">${icon("route")}</span></div><div class="stat-value">${money(fare)}</div><div class="stat-note">${fare === 3400 ? "Domingos y festivos" : "Tarifa ordinaria · lunes a sábado"}</div></article>
    <article class="stat-card"><div class="stat-top"><span class="stat-label">VIAJES REGISTRADOS</span><span class="stat-icon green">${icon("bus")}</span></div><div class="stat-value">${tripCount}</div><div class="stat-note">En la cuenta de demostración</div></article>
    <article class="stat-card"><div class="stat-top"><span class="stat-label">ÚLTIMO MÉTODO</span><span class="stat-icon dark">${icon("clock")}</span></div><div class="stat-value stat-value-method">${escapeHtml(lastMethod)}</div><div class="stat-note">${state.trips.length ? "Tu movimiento más reciente" : "Tu actividad aparecerá aquí"}</div></article>
  </section>
  ${renderWeeklyActivity()}
  <section class="content-grid">
    <div>${pageTable(getRecentTrips())}</div>
    <div class="side-stack">
      <article class="fare-card"><div class="fare-heading"><span>Tarifa vigente</span>${icon("route")}</div><div class="fare-amount">${money(fare)}</div><div class="fare-foot"><span>${fare === 3400 ? "Domingo o festivo" : "Lunes a sábado"}</span><strong>Por viaje</strong></div></article>
      <article class="quick-card"><h2 class="quick-card-heading">¿Qué necesitas hoy?</h2><p class="quick-card-copy">Elige cómo quieres continuar tu viaje.</p><div class="quick-actions">
        <button class="quick-action" data-view="qr">${icon("qr")}<span>Pagar con saldo: escanea el QR del bus</span>${icon("arrow", "icon quick-arrow")}</button>
        <button class="quick-action" data-action="payment" data-method="efectivo">${icon("bus")}<span>Registrar pago en efectivo</span>${icon("arrow", "icon quick-arrow")}</button>
        <button class="quick-action" data-view="recarga">${icon("plus")}<span>Recargar mi saldo</span>${icon("arrow", "icon quick-arrow")}</button>
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
    "Turno y recaudo",
    "Confirma tu jornada, registra cada abordaje y revisa el cuadre del efectivo.",
  );

  if (!shift) {
    activeBusQr = null;
    const latestSummary = latestShift
      ? `<article class="shift-summary-card${latestShift.cashDifference ? " has-difference" : ""}">
          <div class="shift-summary-heading">${icon(latestShift.cashDifference ? "clock" : "check")}<strong>Último turno de demostración</strong></div>
          <div class="shift-summary-grid"><span>${escapeHtml(formatDate(new Date(latestShift.startedAt)))}</span><span>${latestShift.entries.length} ${latestShift.entries.length === 1 ? "abordaje" : "abordajes"}</span><span>Recaudo registrado ${money(latestShift.total)}</span></div>
          <p>${latestShift.cashDifference ? `Diferencia por revisar: ${money(Math.abs(latestShift.cashDifference))} ${latestShift.cashDifference > 0 ? "de más" : "faltante"} (declarado ${money(latestShift.cashCounted)} · anotado ${money(latestShift.cashExpected)}).` : "El efectivo declarado coincide con los pagos registrados."}</p>
        </article>`
      : "";
    return `${heading}
      <section class="driver-shift-hero">
        <div class="driver-shift-copy"><div class="eyebrow">${icon("clock")} ASIGNACIÓN OPERATIVA</div>
          <h2>No hay un turno activo</h2><p>${driverAssignment ? "Confirma el turno que el servidor tiene asignado a tu cuenta para habilitar el registro de abordajes." : "No tienes una asignación pendiente. El historial de cierres sigue disponible; solicita una nueva asignación al administrador."}</p>
        </div>
        <div class="assigned-shift"><span>RUTA ASIGNADA</span><strong>Ruta ${escapeHtml(driverAssignment?.route_name ?? "—")} <i>·</i> Vehículo ${escapeHtml(driverAssignment?.vehicle_plate ?? "—")}</strong><small>Conductor ${escapeHtml(driverAssignment?.driver_name ?? authenticatedUser.names)}</small></div>
        <button class="button button-mint" type="button" data-action="start-driver-shift"${driverAssignment ? "" : " disabled"}>${icon("check")} ${driverAssignment ? "Validar turno y comenzar" : "Sin asignación disponible"}</button>
      </section>
      ${latestSummary}
      <article class="driver-integrity-note">${icon("shield")}<div><strong>Turno asociado a tu cuenta</strong><p>El servidor valida el rol y la ruta asignada antes de activar la jornada. Los cobros con tarjeta siguen siendo simulados: no hay conexión a una terminal POS.</p></div></article>`;
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
      <div class="active-shift-status"><span class="active-shift-pulse"></span> TURNO ACTIVO · DEMO</div>
      <h2>Ruta ${escapeHtml(shift.route)} <span>·</span> Vehículo ${escapeHtml(shift.vehicle)}</h2>
      <p>Inicio registrado ${escapeHtml(formatTime(new Date(shift.startedAt)))} · ${entries.length} ${entries.length === 1 ? "abordaje" : "abordajes"} en esta jornada</p>
      <div class="active-shift-reference">Referencia del servidor: ${escapeHtml(shift.reference)}</div>
    </section>
    <section class="surface detail-card bus-qr-card">
      <h2>QR de abordaje del bus</h2>
      <p>El pasajero escanea este código desde su teléfono. Dura 15 minutos; actualízalo cuando venza.</p>
      ${activeBusQr ? `<img class="qr-real-image" src="${activeBusQr.image}" alt="QR de abordaje para la ruta ${escapeHtml(shift.route)}" /><p>Válido hasta ${escapeHtml(formatTime(activeBusQr.expiresAt))}</p>` : "<p>El QR aparecerá al cargar el turno activo.</p>"}
      <button class="button button-outline" type="button" data-action="refresh-bus-qr">Actualizar código</button>
    </section>
    <section class="driver-totals" aria-label="Recaudo registrado en el turno">
      <article><span>EFECTIVO</span><strong>${money(cashTotal)}</strong><small>${entries.filter((entry) => entry.method === "Efectivo").length} registros</small></article>
      <article><span>QR / SALDO</span><strong>${money(walletTotal)}</strong><small>${entries.filter((entry) => entry.method === "QR / saldo").length} registros</small></article>
      <article><span>TARJETA</span><strong>${money(cardTotal)}</strong><small>${entries.filter((entry) => entry.method === "Tarjeta").length} registros</small></article>
      <article class="driver-total-all"><span>TOTAL DEL TURNO</span><strong>${money(total)}</strong><small>${entries.length} ${entries.length === 1 ? "abordaje anotado" : "abordajes anotados"}</small></article>
    </section>
    <section class="driver-work-grid">
      <article class="driver-capture-card">
        <div class="eyebrow">${icon("plus")} REGISTRO DE ABORDAJE · TURNO ACTIVO</div>
        <h2>¿Cómo pagó el pasajero?</h2>
        <p>Anota el medio recibido para dejar constancia en la bitácora de este turno.</p>
        <div class="driver-payment-actions">
          <button type="button" data-action="driver-payment" data-method="cash">${icon("wallet")}<span><strong>Efectivo</strong><small>Recibido en la unidad</small></span>${icon("arrow")}</button>
          <button type="button" data-action="driver-payment" data-method="card">${icon("card")}<span><strong>Tarjeta</strong><small>Registro de demostración · sin POS</small></span>${icon("arrow")}</button>
        </div>
        <div class="driver-demo-warning">${icon("clock")} El turno y sus registros se guardan en el servidor. La terminal POS aún no está integrada.</div>
      </article>
      <article class="driver-close-card">
        <div class="eyebrow">${icon("check")} CIERRE DE JORNADA</div><h2>Cuadra el efectivo</h2>
        <p>Cuenta el efectivo recibido y compáralo con los <strong>${money(cashTotal)}</strong> anotados en la bitácora.</p>
        <form id="close-driver-shift-form">
          <label for="driver-cash-counted">Efectivo contado en caja (COP)</label>
          <input class="input" id="driver-cash-counted" name="cashCounted" type="number" inputmode="numeric" min="0" step="1" value="${cashTotal}" required />
          <button class="button button-outline" type="submit">Cerrar y revisar turno</button>
        </form>
        <small>El cierre registra cualquier diferencia; no la corrige ni la oculta.</small>
      </article>
    </section>
    <section class="surface driver-ledger">
      <div class="surface-header"><div><h2>Bitácora del turno</h2><p>Registros del servidor en orden de llegada · ${entries.length} ${entries.length === 1 ? "registro" : "registros"}</p></div></div>
      <div class="table-wrap"><table class="trip-table driver-ledger-table">
        <thead><tr><th>Referencia</th><th>Hora</th><th>Medio</th><th>Valor</th></tr></thead>
        <tbody>${rows || `<tr><td class="empty-row" colspan="4">Aún no hay abordajes registrados. Anota cada pago para incluirlo en el cuadre.</td></tr>`}</tbody>
      </table></div>
    </section>
    <article class="driver-integrity-note">${icon("shield")}<div><strong>Bitácora del servidor · medios externos simulados</strong><p>Los recaudos quedan asociados al turno autenticado. Las operaciones QR se debitan en servidor; efectivo se registra manualmente. El pago tarjeta se anota como demostración hasta integrar un POS real.</p></div></article>`;
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
  return `${pageHeading(`${icon("qr")} TU VIAJE`, "Escanear QR del bus", "Paga el abordaje leyendo el código que aparece en la pantalla del bus.")}
    <article class="surface detail-card qr-generation-card">
      <h2>Escanea para abordar</h2>
      <p>El código identifica la ruta y el turno del bus. El valor se descuenta de tu billetera cuando el servidor lo valida.</p>
      <form id="passenger-qr-form" data-idempotency-key="${createIdempotencyKey()}">
        <div class="form-field"><label for="passenger-qr-token">Código del bus</label><input class="input" id="passenger-qr-token" name="token" type="text" minlength="20" maxlength="512" autocomplete="off" autocapitalize="off" spellcheck="false" required /></div>
        <video id="passenger-qr-video" class="qr-camera-preview" playsinline muted hidden></video>
        <div class="modal-actions"><button class="button button-outline" type="button" data-action="scan-passenger-camera">Usar cámara</button><button class="button" type="submit">Pagar y abordar</button></div>
      </form>
    </article>`;
}

function renderTopUp() {
  const amounts = [10000, 20000, 50000, 100000];
  return `${pageHeading(`${icon("wallet")} TU BILLETERA`, "Recarga tu saldo", "Elige un monto para simular una recarga en esta demostración.")}
  <section class="balance-banner"><div><div class="eyebrow">SALDO ACTUAL</div><h2>${money(state.balance)}</h2><p>Disponible en esta sesión de demostración.</p></div>${icon("wallet")}</section>
  <section class="surface detail-card"><h2>Elige cuánto quieres recargar</h2><p>Selecciona una de las opciones rápidas para actualizar tu saldo de prueba.</p><div class="amount-grid">${amounts.map((amount) => `<button class="amount-option" data-action="top-up" data-amount="${amount}"><strong>${money(amount)}</strong><span>Recarga de demostración</span></button>`).join("")}</div>
  <form class="custom-amount" id="custom-top-up"><label for="custom-amount">O escribe otro monto (máximo ${money(500000)})</label><input class="input" id="custom-amount" name="amount" type="number" inputmode="numeric" min="1" max="500000" step="1" placeholder="Ej. 35.000" required /><button class="button" type="submit">${icon("plus")} Recargar</button></form></section>
  <article class="subtle-card section-gap">${icon("shield")}<div><strong>Solo simulación local</strong><p>Esta recarga no mueve dinero real ni está conectada a una entidad financiera.</p></div></article>`;
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

  return `${pageHeading(`${icon("clock")} TU ACTIVIDAD`, "Movimientos y viajes", "Consulta pagos, recargas y traspasos registrados en tu cuenta.")}
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
  <div class="surface"><div class="surface-header"><div><h2>Actividad de tu cuenta</h2><p>Ordenada de la m&aacute;s reciente a la m&aacute;s antigua. Incluye el saldo antes y despu&eacute;s de cada movimiento.</p></div></div>
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
  document.querySelector("#single-profile-label").hidden = hasMultipleRoles;
  document.querySelector("#single-profile-label").textContent = currentProfile === "conductor" ? "Conductor" : "Pasajero";
  document.querySelector("#sidebar-avatar").textContent = initials;
  document.querySelector("#topbar-avatar").textContent = initials;
  document.querySelector("#sidebar-name").textContent = authenticatedUser.names;
  document.querySelector("#sidebar-role").textContent = `${currentProfile === "conductor" ? "Espacio conductor" : "Espacio pasajero"} · demostración`;
  document.querySelector("#breadcrumb-context").textContent = currentProfile === "conductor"
    ? "Cuenta con rol de conductor"
    : "Espacio pasajero";
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
  if (profile === "conductor") {
    try {
      try {
        driverAssignment = await apiRequest("/driver/demo/assignment");
      } catch (error) {
        if (error.status !== 404) throw error;
        driverAssignment = null;
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
  if (!driverAssignment) {
    showToast("No hay una asignación disponible para iniciar.", true);
    return;
  }
  try {
    await apiRequest(`/driver/shift/start?route_id=${driverAssignment.route_id}`, { method: "POST" });
    await refreshDriverShift();
    renderCurrentView();
    showToast("Turno asignado iniciado en el servidor.");
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

async function startQrCamera(formId, inputId, videoId) {
  // La cámara captura el código; el servidor sigue siendo quien lo valida.
  if (!("BarcodeDetector" in window) || !navigator.mediaDevices?.getUserMedia) {
    showToast("Este navegador no ofrece escaneo QR por cámara. Pega el código manualmente.", true);
    return;
  }
  try {
    activeCameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
    const video = document.querySelector(`#${videoId}`);
    video.srcObject = activeCameraStream;
    video.hidden = false;
    await video.play();
    const detector = new BarcodeDetector({ formats: ["qr_code"] });
    const scan = async () => {
      if (!video.isConnected || !activeCameraStream) return;
      const codes = await detector.detect(video);
      if (codes.length) {
        document.querySelector(`#${inputId}`).value = codes[0].rawValue;
        stopQrCamera();
        document.querySelector(`#${formId}`).requestSubmit();
        return;
      }
      scanLoopTimer = window.setTimeout(scan, 200);
    };
    await scan();
  } catch (error) {
    stopQrCamera();
    console.error("No se pudo iniciar el lector QR:", error);
    showToast("No se pudo acceder a la cámara. Comprueba el permiso del navegador.", true);
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
    driverAssignment = null;
    activeBusQr = null;
    renderCurrentView();
    openShiftReceipt(closed);
    showToast(cashDifference
      ? `Cierre guardado. Diferencia de efectivo: ${money(Math.abs(cashDifference))} ${cashDifference > 0 ? "de más" : "faltante"}.`
      : "Cierre guardado: el efectivo declarado coincide con el registro del servidor.");
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
    <div class="modal-kicker">CIERRE DE DEMOSTRACIÓN</div>
    <h2 id="modal-title">Turno consolidado</h2>
    <p>El servidor guardó este cierre y dejó el turno inactivo.</p>
    <div class="receipt-list">
      <div class="detail-row"><span>Referencia del turno</span><strong>${escapeHtml(`TUR-${shift.shift_id}`)}</strong></div>
      <div class="detail-row"><span>Ruta</span><strong>${escapeHtml(shift.route_name)}</strong></div>
      <div class="detail-row"><span>Pasajes registrados</span><strong>${shift.payment_count}</strong></div>
      <div class="detail-row"><span>QR / saldo</span><strong>${money(shift.qr_total)}</strong></div>
      <div class="detail-row"><span>Efectivo anotado</span><strong>${money(shift.cash_total)}</strong></div>
      <div class="detail-row"><span>Tarjeta simulada</span><strong>${money(shift.card_total)}</strong></div>
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
  connectionLabel.textContent = offline ? "Sin conexión · interfaz" : "API de demostración";
}

function updateInstallButton() {
  const isStandalone = window.matchMedia("(display-mode: standalone)").matches
    || window.navigator.standalone === true;
  installButton.hidden = isStandalone || (!deferredInstallPrompt && window.innerWidth > 760);
}

// Diálogos, avisos y acciones que acompañan el recorrido.
function openDemoInfo() {
  modal.classList.add("demo-info-open");
  modalContent.innerHTML = `<article class="demo-info-container">
    <header class="demo-info-header">
      <span class="demo-info-title">${icon("document")}<span id="modal-title">Sobre la demostración</span></span>
      <button class="icon-button demo-info-close" type="button" data-action="close-modal" aria-label="Cerrar información">${icon("close")}</button>
    </header>
    <section class="demo-info-body">
      <span class="demo-info-intro">QrPass está en una etapa inicial de desarrollo.</span>
      <p>Iniciaste sesión con una cuenta de demostración. La API devuelve sus roles y protege cada operación. Solo una cuenta con rol de conductor puede entrar a ese espacio. Si tiene ambos roles, puede cambiar entre espacios: su billetera de pasajero y su turno son independientes.</p>
      <p>Saldo, historial, pagos simulados, códigos QR y turnos se consultan o registran en el backend de demostración; no se conservan como datos autoritativos en este navegador.</p>
      <h3>Qué puedes probar</h3>
      <ul><li>En el espacio pasajero: escanear el QR que muestra el bus, pagar con saldo, consultar el historial y corregir un abordaje en la ruta equivocada mediante un transbordo dentro de las reglas vigentes.</li><li>En el espacio conductor: usar por separado las funciones de pasajero y, por su rol adicional, iniciar el turno asignado, mostrar el QR del bus, registrar efectivo/tarjeta simulados y cerrar el turno con conciliación de efectivo.</li></ul>
      <h3>Qué no hace esta versión</h3>
      <ul><li>No procesa dinero real ni se conecta a un POS o pasarela de pago.</li><li>El QR de abordaje es una demostración firmada por el servidor y requiere conexión para pagar; aún no está integrado con un dispositivo físico instalado en el bus.</li><li>El funcionamiento sin conexión solo conserva la interfaz PWA; no autoriza, valida ni sincroniza pagos offline.</li><li>La tarifa, asignación y reglas operacionales son datos de demostración, no una integración con el operador de transporte.</li></ul>
      <h3>Acerca de tus datos de prueba</h3>
      <p>La API guarda los movimientos de prueba en su base de datos local de desarrollo. No introduzcas información bancaria ni utilices estas credenciales fuera del entorno de demostración.</p>
      <h3>Herramientas de demostración</h3>
      <div style="display:flex; gap:0.5rem; margin-top:0.75rem; flex-wrap:wrap;">
        <button class="button button-outline" type="button" data-action="view-global-metrics"><svg class="icon"><use href="#icon-grid"></use></svg> Ver Métricas Globales (Gerente)</button>
        <button class="button button-outline" type="button" data-action="reset-demo-data"><svg class="icon"><use href="#icon-arrows"></use></svg> Restablecer Datos de Prueba</button>
      </div>
      <div class="demo-info-notice" style="margin-top:1rem;">${icon("shield")}<span>Antes de producción faltan proveedor de pagos, POS, TLS 1.3 en el alojamiento, seguridad de claves y QR offline con firma asimétrica, sincronización y reconciliación, pruebas de carga y revisión legal.</span></div>
    </section>
    <footer class="demo-info-footer"><span>Esta ventana es informativa; cerrarla no representa aceptar términos ni realizar una transacción.</span><button class="button" type="button" data-action="close-modal">Entendido</button></footer>
  </article>`;
  modal.showModal();
}


async function openGlobalMetrics() {
  modal.classList.remove("demo-info-open");
  try {
    const metrics = await apiRequest("/admin/metrics");
    modalContent.innerHTML = `<div class="modal-body">
      <div class="modal-kicker">CONSOLIDADO · GERENCIA DE TRANSPORTE</div>
      <h2 id="modal-title">Métricas Globales de Recaudo</h2>
      <p>Consolidación de todo el recaudo y operación del transporte urbano de Ibagué.</p>
      <div class="receipt-list">
        <div class="receipt-row"><span>Total recaudado</span><strong>${money(metrics.total_collected)}</strong></div>
        <div class="receipt-row"><span>Recaudo en efectivo</span><span>${money(metrics.cash_collected)}</span></div>
        <div class="receipt-row"><span>Recaudo código QR</span><span>${money(metrics.qr_collected)}</span></div>
        <div class="receipt-row"><span>Recaudo tarjeta simulada</span><span>${money(metrics.card_collected)}</span></div>
        <div class="receipt-row"><span>Total viajes</span><span>${metrics.total_trips} abordajes</span></div>
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

async function resetDemoData() {
  try {
    const res = await apiRequest("/admin/demo/reset", { method: "POST" });
    showToast(res.message || "Datos de demostración restablecidos.", "success");
    modal.close();
    await refreshPassengerData();
    if (hasProfileRole("conductor")) {
      try {
        await refreshDriverShift();
      } catch (e) {
        driverState.activeShift = null;
      }
      await refreshDriverShiftHistory();
    }
    renderCurrentView();
  } catch (error) {
    showToast(error.message, "error");
  }
}

function openPrivacyInfo() {
  modal.classList.remove("demo-info-open");
  modalContent.innerHTML = `<div class="modal-body">
    <div class="modal-kicker">PRIVACIDAD · PROTOTIPO</div>
    <h2 id="modal-title">Aviso de privacidad de la demostración</h2>
    <p>Este aviso explica el uso de datos en el prototipo. No es una política de tratamiento aprobada ni reemplaza la revisión legal antes de una operación real.</p>
    <div class="receipt-list">
      <div class="detail-row"><span>Datos de registro</span><strong>Nombre, correo y contraseña</strong></div>
      <div class="detail-row"><span>Datos de uso</span><strong>Saldo, pagos y viajes de prueba</strong></div>
      <div class="detail-row"><span>Para qué se usan</span><strong>Acceso a la cuenta y pruebas de los flujos</strong></div>
      <div class="detail-row"><span>Almacenamiento</span><strong>Base de datos local de demostración</strong></div>
    </div>
    <p>La contraseña se guarda como un hash seguro. No escribas datos bancarios ni uses una contraseña que tengas en otros servicios. Para ejercer derechos sobre datos del prototipo, contacta al responsable del proyecto que te dio acceso.</p>
    <div class="demo-info-notice">${icon("shield")}<span>Antes de usar datos reales se necesita identificar al responsable, definir finalidades y retención, habilitar canales para solicitudes y aprobar el aviso conforme a la normativa aplicable.</span></div>
    <div class="modal-actions"><button class="button" type="button" data-action="close-modal">Cerrar aviso</button></div>
  </div>`;
  modal.showModal();
}

async function installApp() {
  if (!deferredInstallPrompt) {
    modalContent.innerHTML = `<div class="modal-body"><div class="modal-kicker">QRPass EN TU BOLSILLO</div><h2 id="modal-title">Añade QrPass a tu pantalla de inicio</h2><p>Al instalarla podrás abrir la demostración desde un icono, como una app.</p>
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
  // El recibo ayuda a entender qué acaba de pasar, pero siempre deja claro
  // que este prototipo no es un comprobante financiero oficial.
  modalContent.innerHTML = `<div class="modal-body">
    <div class="receipt-mark">${icon("check")}</div><div class="modal-kicker">${isTransfer ? "TRASPASO REGISTRADO" : "MOVIMIENTO REGISTRADO"}</div>
    <h2 id="modal-title">${isTransfer ? "Tu pago fue transferido" : trip.movementType === "top_up" ? "Recarga registrada" : "&iexcl;Listo para seguir!"}</h2>
    <p>Movimiento de demostración registrado por la API. No representa dinero real ni sustituye un comprobante oficial.</p>
    <div class="receipt-list">
      <div class="detail-row"><span>Ruta</span><strong>${escapeHtml(trip.route)}</strong></div>
      <div class="detail-row"><span>Método</span><strong>${escapeHtml(trip.method)}</strong></div>
      <div class="detail-row"><span>Valor simulado</span><strong>${trip.amount ? money(trip.amount) : "Sin costo adicional"}</strong></div>
      <div class="detail-row"><span>Referencia</span><strong>${escapeHtml(trip.code)}</strong></div>
      <div class="detail-row"><span>Fecha y hora</span><strong>${escapeHtml(formatDate(new Date(trip.createdAt)))} · ${escapeHtml(formatTime(new Date(trip.createdAt)))}</strong></div>
    </div>
    <div class="modal-actions"><button class="button" data-action="close-modal">Entendido</button></div>
  </div>`;
  modal.showModal();
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
    <div class="modal-kicker">DETALLE DE DEMOSTRACI&Oacute;N</div>
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
    <div class="modal-kicker">PAGO DE DEMOSTRACIÓN</div><h2 id="modal-title">Registra tu viaje</h2>
    <p>Elige la ruta y el método de pago para guardar un movimiento de prueba.</p>
    <form id="payment-form" data-idempotency-key="${createIdempotencyKey()}">
      <div class="form-field"><label for="payment-route">Ruta que vas a abordar</label><select class="select" id="payment-route" name="route" required><option value="" disabled selected>Selecciona una ruta</option>${routeOptions()}</select></div>
      <fieldset class="payment-fieldset"><legend>Método de pago</legend>
        <div class="method-picker">${paymentMethods.map((option) => `<label class="method-choice">
          <input class="method-radio" type="radio" name="method" value="${option.value}"${method === option.value ? " checked" : ""} />
          <span class="method-tile"><span class="method-radio-indicator"></span>${icon(option.icon, "icon method-icon")}<span class="method-label">${option.label}</span><span class="method-detail">${option.detail}</span></span>
        </label>`).join("")}</div>
      </fieldset>
      <div id="card-type-container">${cardTypeField}</div>
      <div class="modal-total"><span>Valor del pasaje</span><strong>${money(fare)}</strong></div>
      <div class="modal-actions"><button class="button button-outline" type="button" data-action="close-modal">Cancelar</button><button class="button" type="submit">Confirmar movimiento</button></div>
    </form>
  </div>`;
  modal.showModal();
}

function choosePaymentMethod(method) {
  const route = document.querySelector("#payment-route")?.value ?? "";
  openPayment(method);
  const routeInput = document.querySelector("#payment-route");
  if (route && routeInput) routeInput.value = route;
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
  modalContent.innerHTML = `<div class="modal-body"><div class="modal-kicker">CAMBIO DE RUTA · DEMOSTRACIÓN</div><h2 id="modal-title">Transfiere tu pago</h2><p>Si abordaste el bus equivocado, indica la ruta correcta dentro de los 20 minutos. El pago original no se vuelve a cobrar.</p>
    <form id="transfer-form" data-trip-id="${latestPaidTrip.tripId}">
      <div class="validity-row">${icon("arrows")}<span>Pago ${escapeHtml(latestPaidTrip.code)} · Ruta ${escapeHtml(latestPaidTrip.route)} · ${money(latestPaidTrip.amount)}</span></div>
      <div class="form-field section-gap"><label for="transfer-route">Ruta correcta</label><select class="select" id="transfer-route" name="route" required><option value="" disabled selected>Selecciona otra ruta</option>${routeOptions(latestPaidTrip.route)}</select></div>
      <div class="modal-total"><span>Costo adicional simulado</span><strong>${money(0)}</strong></div>
      <div class="modal-actions"><button class="button button-outline" type="button" data-action="close-modal">Cancelar</button><button class="button" type="submit">Confirmar traspaso</button></div>
    </form>
  </div>`;
  modal.showModal();
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
    const receipt = await apiRequest("/demo/account/top-ups", {
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
  if (action === "transfer") openTransfer();
  if (action === "demo-info") openDemoInfo();
  if (action === "privacy-info") openPrivacyInfo();
  if (action === "view-global-metrics") openGlobalMetrics();
  if (action === "reset-demo-data") resetDemoData();
  if (action === "logout") logout();
  if (action === "start-driver-shift") startDriverShift();
  if (action === "refresh-bus-qr") {
    try {
      const qr = await apiRequest("/driver/shift/qr?renew=true", { method: "POST" });
      activeBusQr = { image: qr.image_data_uri, expiresAt: new Date(qr.expires_at) };
      renderCurrentView();
      showToast("QR del bus actualizado.");
    } catch (error) {
      showToast(error.message, true);
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
    <div class="modal-kicker">PAGO CON TARJETA · SIMULACIÓN</div><h2 id="modal-title">Registra un pago POS</h2>
    <p>Se anotará en el turno, pero esta versión aún no se conecta a una terminal bancaria.</p>
    <form id="driver-card-payment-form" data-idempotency-key="${createIdempotencyKey()}">
      <div class="form-field"><label for="driver-card-type">Tipo de tarjeta</label><select class="select" id="driver-card-type" name="cardType" required><option value="" disabled selected>Selecciona una opción</option><option value="debit">Débito</option><option value="credit">Crédito</option></select></div>
      <div class="modal-actions"><button class="button button-outline" type="button" data-action="close-modal">Cancelar</button><button class="button" type="submit">Registrar pago POS simulado</button></div>
    </form>
  </div>`;
  modal.showModal();
}

document.querySelector("#registration-toggle").addEventListener("click", () => {
  const loginForm = document.querySelector("#login-form");
  const registrationForm = document.querySelector("#registration-form");
  const showRegistration = registrationForm.hidden;
  loginForm.hidden = showRegistration;
  registrationForm.hidden = !showRegistration;
  document.querySelector("#registration-toggle").textContent = showRegistration
    ? "Ya tengo una cuenta"
    : "Crear cuenta de pasajero";
  showLoginError();
  document.querySelector("#registration-error").hidden = true;
});

document.querySelector("#login-form").addEventListener("submit", async (event) => {
  // El formulario manda las credenciales, guarda el token y carga el perfil.
  // La API valida la contraseña; el navegador no decide si son correctas.
  event.preventDefault();
  const form = event.currentTarget;
  const submit = form.querySelector('button[type="submit"]');
  const formData = new FormData(form);
  submit.disabled = true;
  submit.textContent = "Verificando acceso…";
  showLoginError();
  try {
    const login = await apiRequest("/auth/login", {
      method: "POST",
      body: JSON.stringify({
        username: formData.get("username"),
        password: formData.get("password"),
      }),
    });
    accessToken = login.access_token;
    const user = await apiRequest("/auth/me");
    sessionStorage.setItem(SESSION_EXPIRY_KEY, String(Date.now() + login.expires_in * 1000));
    sessionStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    await activateSession(user, accessToken);
  } catch (error) {
    logout();
    showLoginError(error.message);
  } finally {
    submit.disabled = false;
    submit.innerHTML = `Iniciar sesión ${icon("arrow")}`;
  }
});

document.querySelector("#registration-form").addEventListener("submit", async (event) => {
  // Registro crea la cuenta en el backend. Después se completa el login normal.
  event.preventDefault();
  const form = event.currentTarget;
  const submit = form.querySelector('button[type="submit"]');
  const formData = new FormData(form);
  submit.disabled = true;
  showLoginError();
  const registrationError = document.querySelector("#registration-error");
  registrationError.hidden = true;
  try {
    const email = String(formData.get("email")).trim().toLowerCase();
    const password = String(formData.get("password"));
    await apiRequest("/auth/register", {
      method: "POST",
      body: JSON.stringify({
        names: formData.get("names"),
        email,
        password,
        privacy_consent: formData.get("privacy_consent") === "on",
      }),
    });
    document.querySelector("#login-username").value = email;
    document.querySelector("#login-password").value = password;
    document.querySelector("#registration-form").hidden = true;
    document.querySelector("#login-form").hidden = false;
    document.querySelector("#registration-toggle").hidden = true;
    document.querySelector("#login-form").requestSubmit();
  } catch (error) {
    registrationError.textContent = error.message;
    registrationError.hidden = false;
  } finally {
    submit.disabled = false;
  }
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
      const result = await apiRequest("/demo/account/qr/validate", {
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
      const receipt = await apiRequest("/demo/account/payments", {
        method: "POST",
        body: JSON.stringify({
          route_id: routeId,
          method: paymentMethods[selectedPaymentMethod],
          ...(selectedPaymentMethod === "tarjeta" ? { card_type: cardTypes[cardType] } : {}),
          idempotency_key: event.target.dataset.idempotencyKey,
        }),
      });
      const trip = {
        route: receipt.route_name,
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
      const transfer = await apiRequest("/demo/account/transfers", {
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

modal.addEventListener("close", () => {
  modal.classList.remove("demo-info-open");
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
      .then(() => console.info("QrPass: soporte de demostración sin conexión activado."))
      .catch((error) => {
        console.error("No se pudo registrar el modo sin conexión de QrPass:", error);
        showToast("No se pudo activar el modo sin conexión en este navegador.", true);
      });
  });
}
