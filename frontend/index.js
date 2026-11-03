const apiClient = window.QrPassApi;

// La entrada valida el rol en el servidor antes de elegir una página de trabajo.
async function routeSession() {
  const token = sessionStorage.getItem(apiClient.ACCESS_TOKEN_KEY);
  if (!token) {
    window.location.replace("./login.html");
    return;
  }

  try {
    const user = await apiClient.request("/auth/me");
    const roles = Array.isArray(user.roles) ? user.roles : [];
    const preferredProfile = sessionStorage.getItem("qrpass-active-profile-v1");
    const profile = preferredProfile && (
      (preferredProfile === "pasajero" && roles.includes("PASSENGER"))
      || (preferredProfile === "conductor" && roles.includes("DRIVER"))
    )
      ? preferredProfile
      : roles.includes("DRIVER") ? "conductor" : "pasajero";

    if (!roles.includes("PASSENGER") && !roles.includes("DRIVER")) {
      throw new Error("La cuenta no tiene un rol habilitado para usar QrPass.");
    }

    window.location.replace(profile === "conductor" ? "./conductor.html" : "./pasajero.html");
  } catch (error) {
    sessionStorage.setItem("qrpass-login-message-v1", error.message);
    if (error.status === 401) {
      sessionStorage.removeItem(apiClient.ACCESS_TOKEN_KEY);
      sessionStorage.removeItem(apiClient.SESSION_EXPIRY_KEY);
    }
    window.location.replace("./login.html?reason=invalid-session");
  }
}

routeSession();
