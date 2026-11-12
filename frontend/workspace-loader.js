const workspaceRoot = document.querySelector("#workspace-root");

// Pasajero y conductor comparten la misma carcasa; cada página aporta su perfil y CSS.
async function loadWorkspace() {
  if (!sessionStorage.getItem(window.QrPassApi.ACCESS_TOKEN_KEY)) {
    window.location.replace("./login.html");
    return;
  }

  try {
    const response = await fetch("./workspace.html?v=6");
    if (!response.ok) {
      throw new Error(`No se pudo cargar el espacio de trabajo (HTTP ${response.status}).`);
    }
    const markup = await response.text();
    if (!markup.trim()) {
      throw new Error("La plantilla del espacio de trabajo está vacía.");
    }

    workspaceRoot.outerHTML = markup;
    const appScript = document.createElement("script");
    appScript.src = "./app.js?v=" + Date.now();
    appScript.onerror = () => {
      console.error("No se pudo cargar el código del espacio de trabajo.");
      document.body.insertAdjacentHTML(
        "afterbegin",
        '<p class="workspace-loading" role="alert">No se pudo iniciar QrPass. Recarga la página para volver a intentarlo.</p>',
      );
    };
    document.body.append(appScript);
  } catch (error) {
    console.error("No se pudo preparar el espacio de trabajo:", error);
    workspaceRoot.className = "workspace-loading workspace-load-error";
    workspaceRoot.setAttribute("role", "alert");
    workspaceRoot.textContent = error.message;
  }
}

loadWorkspace();
