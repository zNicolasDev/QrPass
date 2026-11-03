const apiClient = window.QrPassApi;
const loginForm = document.querySelector("#login-form");
const registrationForm = document.querySelector("#registration-form");
const registrationToggle = document.querySelector("#registration-toggle");

function showError(element, message = "") {
  element.textContent = message;
  element.hidden = !message;
}

function clearSession() {
  sessionStorage.removeItem(apiClient.ACCESS_TOKEN_KEY);
  sessionStorage.removeItem(apiClient.SESSION_EXPIRY_KEY);
}

const reason = new URLSearchParams(window.location.search).get("reason");
const savedMessage = sessionStorage.getItem("qrpass-login-message-v1");
sessionStorage.removeItem("qrpass-login-message-v1");
if (savedMessage) {
  showError(document.querySelector("#login-error"), savedMessage);
} else if (reason === "expired") {
  showError(document.querySelector("#login-error"), "La sesión venció. Inicia sesión otra vez.");
} else if (reason === "invalid-session") {
  showError(document.querySelector("#login-error"), "La sesión ya no es válida. Inicia sesión otra vez.");
}

registrationToggle.addEventListener("click", () => {
  const showRegistration = registrationForm.hidden;
  loginForm.hidden = showRegistration;
  registrationForm.hidden = !showRegistration;
  registrationToggle.textContent = showRegistration ? "Ya tengo una cuenta" : "Crear cuenta de pasajero";
  showError(document.querySelector("#login-error"));
  showError(document.querySelector("#registration-error"));
});

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const submit = form.querySelector('button[type="submit"]');
  const formData = new FormData(form);
  submit.disabled = true;
  submit.textContent = "Verificando acceso…";
  showError(document.querySelector("#login-error"));

  try {
    const login = await apiClient.request("/auth/login", {
      method: "POST",
      body: JSON.stringify({
        username: formData.get("username"),
        password: formData.get("password"),
      }),
    });
    sessionStorage.setItem(apiClient.ACCESS_TOKEN_KEY, login.access_token);
    sessionStorage.setItem(apiClient.SESSION_EXPIRY_KEY, String(Date.now() + login.expires_in * 1000));
    await apiClient.request("/auth/me");
    window.location.replace("./index.html");
  } catch (error) {
    clearSession();
    showError(document.querySelector("#login-error"), error.message);
  } finally {
    submit.disabled = false;
    submit.innerHTML = 'Iniciar sesión <svg class="icon"><use href="#icon-arrow" /></svg>';
  }
});

registrationForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const submit = form.querySelector('button[type="submit"]');
  const formData = new FormData(form);
  const registrationError = document.querySelector("#registration-error");
  submit.disabled = true;
  showError(registrationError);

  try {
    const email = String(formData.get("email")).trim().toLowerCase();
    const password = String(formData.get("password"));
    await apiClient.request("/auth/register", {
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
    registrationForm.hidden = true;
    loginForm.hidden = false;
    registrationToggle.hidden = true;
    loginForm.requestSubmit();
  } catch (error) {
    showError(registrationError, error.message);
  } finally {
    submit.disabled = false;
  }
});

const privacyDialog = document.querySelector("#privacy-dialog");
document.querySelector("#privacy-link").addEventListener("click", () => privacyDialog.showModal());
document.querySelector("#close-privacy").addEventListener("click", () => privacyDialog.close());
