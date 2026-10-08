import tkinter as tk
from tkinter import messagebox, ttk
import random
import datetime


class SistemaPagoQR:
    """
    Sistema de pago para transporte público - Ibagué.
    Proyecto académico - Ingeniería de Sistemas.

    Permite generar códigos QR de viaje, pagar con saldo, en efectivo,
    con tarjeta (débito o crédito) y transferir un pago ya realizado
    hacia otra buseta cuando el usuario abordó una ruta equivocada.
    """

    # ------------------------------------------------------------------
    # Paleta de colores y tipografías (definidas una sola vez)
    # ------------------------------------------------------------------
    COLOR_FONDO_HEADER = "#10233F"
    COLOR_SIDEBAR = "#16304F"
    COLOR_SIDEBAR_HOVER = "#1F4368"
    COLOR_SIDEBAR_ACTIVO = "#2A5C8A"
    COLOR_CONTENIDO = "#EEF1F5"
    COLOR_TARJETA = "#FFFFFF"
    COLOR_BORDE = "#D6DCE3"
    COLOR_TEXTO_CLARO = "#F2F4F7"
    COLOR_TEXTO_SECUNDARIO = "#9FB3C8"
    COLOR_TEXTO_OSCURO = "#1E2A38"
    COLOR_ACENTO = "#1E7A6F"
    COLOR_ACENTO_OSCURO = "#155A52"
    COLOR_ADVERTENCIA = "#B8860B"
    COLOR_ERROR = "#B23A48"
    COLOR_EFECTIVO = "#3E7C4A"
    COLOR_TARJETA_BTN = "#2E5FA3"
    COLOR_TRASPASO = "#8A5A2E"

    FUENTE_LOGO = ("Segoe UI", 15, "bold")
    FUENTE_SLOGAN = ("Segoe UI", 8)
    FUENTE_RELOJ = ("Consolas", 11)
    FUENTE_SIDEBAR = ("Segoe UI", 10)
    FUENTE_TITULO = ("Segoe UI", 15, "bold")
    FUENTE_SUBTITULO = ("Segoe UI", 11, "bold")
    FUENTE_TEXTO = ("Segoe UI", 10)
    FUENTE_TEXTO_CHICA = ("Segoe UI", 9)
    FUENTE_VALOR = ("Segoe UI", 18, "bold")

    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("SISTUR Ibagué - Sistema de Recaudo Electrónico")
        self.ventana.geometry("1000x650")
        self.ventana.minsize(940, 600)
        self.ventana.configure(bg=self.COLOR_CONTENIDO)

        # ---------------- Datos del sistema ----------------
        self.saldo_usuario = 50000
        self.tarifa_semana = 3300
        self.tarifa_fin_semana = 3400
        self.historial_viajes = []
        self.codigo_qr_actual = None
        self.vista_activa = None
        self.boton_activo = None

        self.rutas_disponibles = [
            "1", "2", "4/7", "6", "8/39", "9", "11", "14", "15", "17",
            "18", "19", "20", "21", "22", "23", "24", "28", "29", "31",
            "33", "35", "37", "40", "43", "48", "50", "53", "82"
        ]

        self._construir_interfaz()
        self.mostrar_inicio()
        self._actualizar_reloj()

    # ------------------------------------------------------------------
    # Utilidades generales
    # ------------------------------------------------------------------
    def obtener_tarifa_actual(self):
        hoy = datetime.date.today()
        if hoy.weekday() >= 5:
            return self.tarifa_fin_semana
        return self.tarifa_semana

    def _limpiar_contenido(self):
        for widget in self.frame_contenido.winfo_children():
            widget.destroy()

    def _actualizar_header(self):
        tarifa_actual = self.obtener_tarifa_actual()
        tipo_dia = "Fin de semana / Festivo" if tarifa_actual == self.tarifa_fin_semana else "Lunes a viernes"
        self.label_saldo_header.config(text=f"Saldo disponible: ${self.saldo_usuario:,}")
        self.label_tarifa_header.config(text=f"Tarifa vigente ({tipo_dia}): ${tarifa_actual:,}")

    def _actualizar_reloj(self):
        ahora = datetime.datetime.now().strftime("%A %d/%m/%Y   %H:%M:%S")
        self.label_reloj.config(text=ahora.upper())
        self.ventana.after(1000, self._actualizar_reloj)

    def _generar_codigo(self, prefijo="IBG"):
        return f"{prefijo}-{random.randint(100000, 999999)}"

    # ------------------------------------------------------------------
    # Construcción de la interfaz base: encabezado + barra lateral + contenido
    # ------------------------------------------------------------------
    def _construir_interfaz(self):
        self._construir_header()

        contenedor = tk.Frame(self.ventana, bg=self.COLOR_CONTENIDO)
        contenedor.pack(fill="both", expand=True)

        self._construir_sidebar(contenedor)

        self.frame_contenido = tk.Frame(contenedor, bg=self.COLOR_CONTENIDO)
        self.frame_contenido.pack(side="left", fill="both", expand=True, padx=24, pady=20)

    def _construir_header(self):
        header = tk.Frame(self.ventana, bg=self.COLOR_FONDO_HEADER, height=72)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        # Bloque de identidad del sistema
        bloque_logo = tk.Frame(header, bg=self.COLOR_FONDO_HEADER)
        bloque_logo.pack(side="left", padx=22)

        marca = tk.Frame(bloque_logo, bg=self.COLOR_ACENTO, width=6)
        marca.pack(side="left", fill="y", pady=14)

        texto_logo = tk.Frame(bloque_logo, bg=self.COLOR_FONDO_HEADER)
        texto_logo.pack(side="left", padx=10)

        tk.Label(texto_logo, text="SISTUR IBAGUÉ", font=self.FUENTE_LOGO,
                 fg=self.COLOR_TEXTO_CLARO, bg=self.COLOR_FONDO_HEADER).pack(anchor="w", pady=(10, 0))
        tk.Label(texto_logo, text="Sistema Integrado de Recaudo Electrónico - Transporte Público",
                 font=self.FUENTE_SLOGAN, fg=self.COLOR_TEXTO_SECUNDARIO,
                 bg=self.COLOR_FONDO_HEADER).pack(anchor="w")

        # Reloj (información del turno actual)
        self.label_reloj = tk.Label(header, text="", font=self.FUENTE_RELOJ,
                                     fg=self.COLOR_TEXTO_SECUNDARIO, bg=self.COLOR_FONDO_HEADER)
        self.label_reloj.pack(side="left", padx=30)

        # Bloque de saldo y tarifa (a la derecha)
        bloque_estado = tk.Frame(header, bg=self.COLOR_FONDO_HEADER)
        bloque_estado.pack(side="right", padx=24)

        self.label_saldo_header = tk.Label(bloque_estado, text="", font=("Segoe UI", 11, "bold"),
                                            fg=self.COLOR_TEXTO_CLARO, bg=self.COLOR_FONDO_HEADER)
        self.label_saldo_header.pack(anchor="e", pady=(14, 0))

        self.label_tarifa_header = tk.Label(bloque_estado, text="", font=self.FUENTE_TEXTO_CHICA,
                                             fg=self.COLOR_TEXTO_SECUNDARIO, bg=self.COLOR_FONDO_HEADER)
        self.label_tarifa_header.pack(anchor="e")

        self._actualizar_header()

    def _construir_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg=self.COLOR_SIDEBAR, width=230)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="MENÚ PRINCIPAL", font=("Segoe UI", 9, "bold"),
                 fg=self.COLOR_TEXTO_SECUNDARIO, bg=self.COLOR_SIDEBAR).pack(anchor="w", padx=20, pady=(22, 8))

        self.botones_sidebar = {}
        opciones = [
            ("inicio", "Panel principal", self.mostrar_inicio),
            ("qr", "Generar código QR", self.generar_qr),
            ("saldo", "Pago con saldo", self.pago_con_saldo),
            ("efectivo", "Pago en efectivo", self.pago_efectivo),
            ("tarjeta", "Pago con tarjeta", self.pago_tarjeta),
            ("traspaso", "Traspaso entre rutas", self.traspaso_ruta),
            ("recarga", "Recargar saldo", self.recargar_saldo),
            ("historial", "Historial de viajes", self.ver_historial),
        ]

        for clave, texto, comando in opciones:
            self.botones_sidebar[clave] = self._crear_boton_sidebar(sidebar, texto, comando, clave)

        pie = tk.Label(sidebar, text="Proyecto académico\nIngeniería de Sistemas",
                        font=("Segoe UI", 8), fg=self.COLOR_TEXTO_SECUNDARIO,
                        bg=self.COLOR_SIDEBAR, justify="left")
        pie.pack(side="bottom", anchor="w", padx=20, pady=16)

    def _crear_boton_sidebar(self, parent, texto, comando, clave):
        boton = tk.Label(parent, text=texto, font=self.FUENTE_SIDEBAR, anchor="w",
                          fg=self.COLOR_TEXTO_CLARO, bg=self.COLOR_SIDEBAR,
                          padx=20, pady=12, cursor="hand2")
        boton.pack(fill="x")

        def al_entrar(event):
            if self.boton_activo != clave:
                boton.config(bg=self.COLOR_SIDEBAR_HOVER)

        def al_salir(event):
            if self.boton_activo != clave:
                boton.config(bg=self.COLOR_SIDEBAR)

        def al_click(event):
            self._marcar_boton_activo(clave)
            comando()

        boton.bind("<Enter>", al_entrar)
        boton.bind("<Leave>", al_salir)
        boton.bind("<Button-1>", al_click)
        return boton

    def _marcar_boton_activo(self, clave):
        for k, boton in self.botones_sidebar.items():
            boton.config(bg=self.COLOR_SIDEBAR_ACTIVO if k == clave else self.COLOR_SIDEBAR)
        self.boton_activo = clave

    # ------------------------------------------------------------------
    # Componentes reutilizables
    # ------------------------------------------------------------------
    def _titulo_seccion(self, parent, titulo, subtitulo=""):
        bloque = tk.Frame(parent, bg=self.COLOR_CONTENIDO)
        bloque.pack(fill="x", pady=(0, 16))
        tk.Label(bloque, text=titulo, font=self.FUENTE_TITULO, fg=self.COLOR_TEXTO_OSCURO,
                  bg=self.COLOR_CONTENIDO).pack(anchor="w")
        if subtitulo:
            tk.Label(bloque, text=subtitulo, font=self.FUENTE_TEXTO_CHICA, fg="#5B6B7C",
                      bg=self.COLOR_CONTENIDO).pack(anchor="w", pady=(2, 0))
        linea = tk.Frame(bloque, bg=self.COLOR_ACENTO, height=3, width=60)
        linea.pack(anchor="w", pady=(8, 0))

    def _tarjeta(self, parent, **kwargs):
        borde = tk.Frame(parent, bg=self.COLOR_BORDE)
        interior = tk.Frame(borde, bg=self.COLOR_TARJETA)
        interior.pack(fill="both", expand=True, padx=1, pady=1)
        return borde, interior

    def _boton_accion(self, parent, texto, comando, color, ancho=24):
        return tk.Button(parent, text=texto, command=comando, font=("Segoe UI", 10, "bold"),
                          bg=color, fg="white", activebackground=color, activeforeground="white",
                          relief="flat", bd=0, width=ancho, height=2, cursor="hand2")

    def _crear_ventana_modal(self, titulo, ancho, alto):
        ventana = tk.Toplevel(self.ventana)
        ventana.title(titulo)
        ventana.geometry(f"{ancho}x{alto}")
        ventana.configure(bg=self.COLOR_TARJETA)
        ventana.resizable(False, False)
        ventana.grab_set()
        ventana.transient(self.ventana)
        return ventana

    # ------------------------------------------------------------------
    # Vista: Panel principal
    # ------------------------------------------------------------------
    def mostrar_inicio(self):
        self._limpiar_contenido()
        self._actualizar_header()
        self._marcar_boton_activo("inicio")

        self._titulo_seccion(self.frame_contenido, "Panel principal",
                              "Resumen del estado actual de la cuenta y del servicio")

        fila_tarjetas = tk.Frame(self.frame_contenido, bg=self.COLOR_CONTENIDO)
        fila_tarjetas.pack(fill="x", pady=(0, 20))

        tarifa_actual = self.obtener_tarifa_actual()
        total_viajes = len(self.historial_viajes)
        ultimo = self.historial_viajes[-1] if self.historial_viajes else None
        ultimo_metodo = ultimo["metodo"] if ultimo else "Sin registros"

        datos_tarjetas = [
            ("SALDO DISPONIBLE", f"${self.saldo_usuario:,}", self.COLOR_ACENTO),
            ("TARIFA VIGENTE", f"${tarifa_actual:,}", self.COLOR_TARJETA_BTN),
            ("VIAJES REGISTRADOS", f"{total_viajes}", self.COLOR_TRASPASO),
            ("ÚLTIMO MÉTODO DE PAGO", ultimo_metodo, self.COLOR_EFECTIVO),
        ]

        for i, (etiqueta, valor, color) in enumerate(datos_tarjetas):
            borde, tarjeta = self._tarjeta(fila_tarjetas)
            borde.grid(row=0, column=i, padx=(0, 14) if i < 3 else 0, sticky="nsew")
            fila_tarjetas.grid_columnconfigure(i, weight=1)

            franja = tk.Frame(tarjeta, bg=color, height=4)
            franja.pack(fill="x")
            tk.Label(tarjeta, text=etiqueta, font=("Segoe UI", 8, "bold"), fg="#5B6B7C",
                      bg=self.COLOR_TARJETA).pack(anchor="w", padx=16, pady=(14, 2))
            tk.Label(tarjeta, text=valor, font=self.FUENTE_VALOR, fg=self.COLOR_TEXTO_OSCURO,
                      bg=self.COLOR_TARJETA, wraplength=180, justify="left").pack(anchor="w", padx=16, pady=(0, 16))

        # Bloque informativo de métodos de pago disponibles
        borde_info, info = self._tarjeta(self.frame_contenido)
        borde_info.pack(fill="both", expand=True)

        tk.Label(info, text="Métodos de pago habilitados en este terminal", font=self.FUENTE_SUBTITULO,
                  fg=self.COLOR_TEXTO_OSCURO, bg=self.COLOR_TARJETA).pack(anchor="w", padx=20, pady=(18, 6))

        descripciones = [
            "Saldo (QR): descuenta el valor del pasaje del saldo cargado en la cuenta del usuario.",
            "Efectivo: se registra el viaje sin afectar el saldo; el conductor recibe el pago en el vehículo.",
            "Tarjeta débito / crédito: simula el cobro mediante datáfono, sin afectar el saldo en cuenta.",
            "Traspaso entre rutas: permite trasladar un pago ya realizado hacia la buseta correcta, sin cobro adicional, cuando el usuario abordó una ruta equivocada.",
        ]
        for texto in descripciones:
            fila = tk.Frame(info, bg=self.COLOR_TARJETA)
            fila.pack(fill="x", padx=20, pady=4, anchor="w")
            tk.Label(fila, text="-", font=self.FUENTE_TEXTO, fg=self.COLOR_ACENTO,
                      bg=self.COLOR_TARJETA).pack(side="left", anchor="n")
            tk.Label(fila, text=texto, font=self.FUENTE_TEXTO_CHICA, fg="#3D4A57",
                      bg=self.COLOR_TARJETA, wraplength=700, justify="left").pack(side="left", padx=6)

        tk.Label(info, text="", bg=self.COLOR_TARJETA).pack(pady=6)

    # ------------------------------------------------------------------
    # Vista: Generar código QR
    # ------------------------------------------------------------------
    def generar_qr(self):
        self._limpiar_contenido()
        self._marcar_boton_activo("qr")
        self._titulo_seccion(self.frame_contenido, "Generar código QR",
                              "Código temporal para validar el ingreso al vehículo")

        contenedor = tk.Frame(self.frame_contenido, bg=self.COLOR_CONTENIDO)
        contenedor.pack(fill="both", expand=True)

        borde_qr, panel_qr = self._tarjeta(contenedor)
        borde_qr.pack(side="left", padx=(0, 16), fill="y")

        codigo_viaje = self._generar_codigo("QR")
        self.codigo_qr_actual = codigo_viaje
        fecha_actual = datetime.datetime.now()

        qr_visual = self._patron_qr()
        tk.Label(panel_qr, text=qr_visual, font=("Consolas", 7), bg=self.COLOR_TARJETA,
                  fg=self.COLOR_TEXTO_OSCURO, justify="left").pack(padx=24, pady=24)

        borde_info, panel_info = self._tarjeta(contenedor)
        borde_info.pack(side="left", fill="both", expand=True)

        tk.Label(panel_info, text="Detalle del código generado", font=self.FUENTE_SUBTITULO,
                  fg=self.COLOR_TEXTO_OSCURO, bg=self.COLOR_TARJETA).pack(anchor="w", padx=20, pady=(20, 10))

        datos = [
            ("Código de viaje", codigo_viaje),
            ("Fecha de generación", fecha_actual.strftime("%Y-%m-%d %H:%M:%S")),
            ("Válido hasta", (fecha_actual + datetime.timedelta(minutes=15)).strftime("%H:%M")),
            ("Tarifa asociada", f"${self.obtener_tarifa_actual():,}"),
        ]
        for etiqueta, valor in datos:
            fila = tk.Frame(panel_info, bg=self.COLOR_TARJETA)
            fila.pack(fill="x", padx=20, pady=4)
            tk.Label(fila, text=f"{etiqueta}:", font=self.FUENTE_TEXTO, fg="#5B6B7C",
                      bg=self.COLOR_TARJETA, width=20, anchor="w").pack(side="left")
            tk.Label(fila, text=valor, font=("Segoe UI", 10, "bold"), fg=self.COLOR_TEXTO_OSCURO,
                      bg=self.COLOR_TARJETA, anchor="w").pack(side="left")

        estado = tk.Frame(panel_info, bg="#E4F3EF")
        estado.pack(fill="x", padx=20, pady=(16, 20))
        tk.Label(estado, text="Estado: código listo para ser escaneado por el validador del vehículo",
                  font=("Segoe UI", 9, "bold"), fg=self.COLOR_ACENTO_OSCURO, bg="#E4F3EF").pack(padx=10, pady=8)

    def _patron_qr(self):
        return """
██████████████  ██  ██████████████
██          ██      ██          ██
██  ██████  ██  ██  ██  ██████  ██
██  ██████  ██      ██  ██████  ██
██  ██████  ██  ██  ██  ██████  ██
██          ██  ██  ██          ██
██████████████  ██  ██████████████
                ██                
████  ██    ████████    ██  ██████
    ██████████    ██████████      
██████      ██████████    ████████
  ██    ████████  ████████  ██    
██  ████    ██████    ████████  ██
                ██                
██████████████    ████  ██  ██████
██          ██████  ██████    ████
██  ██████  ██    ██████  ████████
██  ██████  ██  ████    ██████    
██  ██████  ██████████████  ██████
██          ██    ██    ██████████
██████████████  ████████  ████  ██
        """.strip()

    # ------------------------------------------------------------------
    # Selector de ruta genérico (usado por varios métodos de pago)
    # ------------------------------------------------------------------
    def _selector_ruta(self, ventana, texto_instruccion):
        tk.Label(ventana, text=texto_instruccion, font=self.FUENTE_TEXTO,
                  bg=self.COLOR_TARJETA, fg=self.COLOR_TEXTO_OSCURO).pack(pady=(6, 4))
        combo = ttk.Combobox(ventana, font=self.FUENTE_TEXTO, width=18, state="readonly")
        combo["values"] = tuple(f"Ruta {r}" for r in self.rutas_disponibles)
        combo.pack(pady=6)
        combo.set("Seleccionar ruta...")
        return combo

    # ------------------------------------------------------------------
    # Pago con saldo
    # ------------------------------------------------------------------
    def pago_con_saldo(self):
        self._marcar_boton_activo("saldo")
        ventana = self._crear_ventana_modal("Pago con saldo", 360, 380)

        tk.Label(ventana, text="PAGO CON SALDO", font=self.FUENTE_SUBTITULO,
                  bg=self.COLOR_TARJETA, fg=self.COLOR_TEXTO_OSCURO).pack(pady=(20, 4))

        tarifa_actual = self.obtener_tarifa_actual()
        tk.Label(ventana, text=f"Valor del pasaje: ${tarifa_actual:,}", font=self.FUENTE_TEXTO,
                  bg=self.COLOR_TARJETA, fg=self.COLOR_ACENTO_OSCURO).pack(pady=(0, 6))
        tk.Label(ventana, text=f"Saldo disponible: ${self.saldo_usuario:,}", font=self.FUENTE_TEXTO_CHICA,
                  bg=self.COLOR_TARJETA, fg="#5B6B7C").pack()

        combo = self._selector_ruta(ventana, "Seleccione la ruta que va a abordar:")

        def confirmar():
            if combo.get() == "Seleccionar ruta...":
                messagebox.showwarning("Ruta no seleccionada", "Debe seleccionar una ruta antes de continuar.")
                return
            if self.saldo_usuario < tarifa_actual:
                messagebox.showwarning("Saldo insuficiente",
                                        f"Saldo actual: ${self.saldo_usuario:,}\n"
                                        f"Tarifa requerida: ${tarifa_actual:,}\n\n"
                                        f"Recargue su saldo para continuar.")
                return

            self.saldo_usuario -= tarifa_actual
            viaje = {
                "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "ruta": combo.get(),
                "valor": tarifa_actual,
                "codigo": self.codigo_qr_actual if self.codigo_qr_actual else self._generar_codigo("QR"),
                "metodo": "Saldo (QR)",
            }
            self.historial_viajes.append(viaje)
            self._actualizar_header()
            ventana.destroy()
            self._mostrar_confirmacion(viaje)

        self._boton_accion(ventana, "Confirmar pago", confirmar, self.COLOR_ACENTO, ancho=22).pack(pady=(18, 6))
        tk.Button(ventana, text="Cancelar", command=ventana.destroy, font=self.FUENTE_TEXTO_CHICA,
                   bg=self.COLOR_TARJETA, fg="#5B6B7C", relief="flat", cursor="hand2").pack()

    # ------------------------------------------------------------------
    # Pago en efectivo
    # ------------------------------------------------------------------
    def pago_efectivo(self):
        self._marcar_boton_activo("efectivo")
        ventana = self._crear_ventana_modal("Pago en efectivo", 360, 360)

        tk.Label(ventana, text="PAGO EN EFECTIVO", font=self.FUENTE_SUBTITULO,
                  bg=self.COLOR_TARJETA, fg=self.COLOR_TEXTO_OSCURO).pack(pady=(20, 4))

        tarifa_actual = self.obtener_tarifa_actual()
        tk.Label(ventana, text=f"Valor a recibir por el conductor: ${tarifa_actual:,}",
                  font=self.FUENTE_TEXTO, bg=self.COLOR_TARJETA, fg=self.COLOR_EFECTIVO,
                  wraplength=300, justify="center").pack(pady=(0, 6))
        tk.Label(ventana, text="Este pago no descuenta saldo de la cuenta del usuario.",
                  font=self.FUENTE_TEXTO_CHICA, bg=self.COLOR_TARJETA, fg="#5B6B7C",
                  wraplength=300, justify="center").pack(pady=(0, 6))

        combo = self._selector_ruta(ventana, "Seleccione la ruta abordada:")

        def confirmar():
            if combo.get() == "Seleccionar ruta...":
                messagebox.showwarning("Ruta no seleccionada", "Debe seleccionar una ruta antes de continuar.")
                return

            viaje = {
                "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "ruta": combo.get(),
                "valor": tarifa_actual,
                "codigo": self._generar_codigo("EFE"),
                "metodo": "Efectivo",
            }
            self.historial_viajes.append(viaje)
            self._actualizar_header()
            ventana.destroy()
            self._mostrar_confirmacion(viaje)

        self._boton_accion(ventana, "Registrar pago en efectivo", confirmar,
                             self.COLOR_EFECTIVO, ancho=24).pack(pady=(18, 6))
        tk.Button(ventana, text="Cancelar", command=ventana.destroy, font=self.FUENTE_TEXTO_CHICA,
                   bg=self.COLOR_TARJETA, fg="#5B6B7C", relief="flat", cursor="hand2").pack()

    # ------------------------------------------------------------------
    # Pago con tarjeta (débito / crédito)
    # ------------------------------------------------------------------
    def pago_tarjeta(self):
        self._marcar_boton_activo("tarjeta")
        ventana = self._crear_ventana_modal("Pago con tarjeta", 380, 460)

        tk.Label(ventana, text="PAGO CON TARJETA", font=self.FUENTE_SUBTITULO,
                  bg=self.COLOR_TARJETA, fg=self.COLOR_TEXTO_OSCURO).pack(pady=(20, 4))

        tarifa_actual = self.obtener_tarifa_actual()
        tk.Label(ventana, text=f"Valor del pasaje: ${tarifa_actual:,}", font=self.FUENTE_TEXTO,
                  bg=self.COLOR_TARJETA, fg=self.COLOR_TARJETA_BTN).pack(pady=(0, 10))

        combo = self._selector_ruta(ventana, "Seleccione la ruta que va a abordar:")

        tk.Label(ventana, text="Tipo de tarjeta:", font=self.FUENTE_TEXTO,
                  bg=self.COLOR_TARJETA, fg=self.COLOR_TEXTO_OSCURO).pack(pady=(16, 6))

        tipo_tarjeta = tk.StringVar(value="")
        frame_tipo = tk.Frame(ventana, bg=self.COLOR_TARJETA)
        frame_tipo.pack(pady=4)

        def seleccionar_tipo(valor, boton_seleccionado, boton_otro):
            tipo_tarjeta.set(valor)
            boton_seleccionado.config(bg=self.COLOR_TARJETA_BTN, fg="white")
            boton_otro.config(bg="#E4E9F0", fg=self.COLOR_TEXTO_OSCURO)

        btn_debito = tk.Button(frame_tipo, text="Débito", font=("Segoe UI", 10, "bold"),
                                 bg="#E4E9F0", fg=self.COLOR_TEXTO_OSCURO, width=12, height=2,
                                 relief="flat", cursor="hand2")
        btn_credito = tk.Button(frame_tipo, text="Crédito", font=("Segoe UI", 10, "bold"),
                                  bg="#E4E9F0", fg=self.COLOR_TEXTO_OSCURO, width=12, height=2,
                                  relief="flat", cursor="hand2")
        btn_debito.config(command=lambda: seleccionar_tipo("Débito", btn_debito, btn_credito))
        btn_credito.config(command=lambda: seleccionar_tipo("Crédito", btn_credito, btn_debito))
        btn_debito.grid(row=0, column=0, padx=6)
        btn_credito.grid(row=0, column=1, padx=6)

        label_estado = tk.Label(ventana, text="", font=self.FUENTE_TEXTO_CHICA,
                                  bg=self.COLOR_TARJETA, fg="#5B6B7C")
        label_estado.pack(pady=(14, 0))

        def confirmar():
            if combo.get() == "Seleccionar ruta...":
                messagebox.showwarning("Ruta no seleccionada", "Debe seleccionar una ruta antes de continuar.")
                return
            if tipo_tarjeta.get() == "":
                messagebox.showwarning("Tipo de tarjeta no seleccionado",
                                        "Debe indicar si el pago es con tarjeta débito o crédito.")
                return

            label_estado.config(text="Procesando transacción con el datáfono...")
            ventana.update_idletasks()

            def finalizar():
                viaje = {
                    "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "ruta": combo.get(),
                    "valor": tarifa_actual,
                    "codigo": self._generar_codigo("TAR"),
                    "metodo": f"Tarjeta {tipo_tarjeta.get()}",
                }
                self.historial_viajes.append(viaje)
                self._actualizar_header()
                ventana.destroy()
                self._mostrar_confirmacion(viaje)

            ventana.after(900, finalizar)

        self._boton_accion(ventana, "Confirmar pago", confirmar, self.COLOR_TARJETA_BTN,
                             ancho=22).pack(pady=(14, 6))
        tk.Button(ventana, text="Cancelar", command=ventana.destroy, font=self.FUENTE_TEXTO_CHICA,
                   bg=self.COLOR_TARJETA, fg="#5B6B7C", relief="flat", cursor="hand2").pack()

    # ------------------------------------------------------------------
    # Traspaso de pago entre rutas
    # ------------------------------------------------------------------
    def traspaso_ruta(self):
        self._marcar_boton_activo("traspaso")

        if not self.historial_viajes:
            messagebox.showinfo("Sin viajes registrados",
                                 "No hay ningún pago previo registrado para transferir.\n\n"
                                 "El traspaso solo aplica cuando el usuario ya pagó un pasaje "
                                 "y abordó una ruta distinta a la que necesitaba.")
            return

        ultimo_viaje = self.historial_viajes[-1]

        ventana = self._crear_ventana_modal("Traspaso entre rutas", 400, 440)

        tk.Label(ventana, text="TRASPASO ENTRE RUTAS", font=self.FUENTE_SUBTITULO,
                  bg=self.COLOR_TARJETA, fg=self.COLOR_TEXTO_OSCURO).pack(pady=(20, 4))
        tk.Label(ventana, text="Use esta opción cuando el pasajero abordó una ruta\n"
                                "equivocada y necesita continuar su viaje en otra buseta,\n"
                                "sin realizar un nuevo pago.",
                  font=self.FUENTE_TEXTO_CHICA, bg=self.COLOR_TARJETA, fg="#5B6B7C",
                  justify="center").pack(pady=(0, 12))

        borde_ref, panel_ref = self._tarjeta(ventana)
        borde_ref.pack(padx=24, fill="x")
        tk.Label(panel_ref, text="Pago original registrado", font=("Segoe UI", 9, "bold"),
                  bg=self.COLOR_TARJETA, fg=self.COLOR_TRASPASO).pack(anchor="w", padx=14, pady=(10, 2))
        tk.Label(panel_ref, text=f"Ruta abordada: {ultimo_viaje['ruta']}", font=self.FUENTE_TEXTO_CHICA,
                  bg=self.COLOR_TARJETA, fg=self.COLOR_TEXTO_OSCURO).pack(anchor="w", padx=14)
        tk.Label(panel_ref, text=f"Código de pago: {ultimo_viaje['codigo']}", font=self.FUENTE_TEXTO_CHICA,
                  bg=self.COLOR_TARJETA, fg=self.COLOR_TEXTO_OSCURO).pack(anchor="w", padx=14)
        tk.Label(panel_ref, text=f"Valor ya cancelado: ${ultimo_viaje['valor']:,}", font=self.FUENTE_TEXTO_CHICA,
                  bg=self.COLOR_TARJETA, fg=self.COLOR_TEXTO_OSCURO).pack(anchor="w", padx=14, pady=(0, 10))

        combo = self._selector_ruta(ventana, "Seleccione la ruta correcta a la que se transfiere el pago:")

        def confirmar():
            ruta_nueva = combo.get()
            if ruta_nueva == "Seleccionar ruta...":
                messagebox.showwarning("Ruta no seleccionada", "Debe seleccionar la ruta correcta.")
                return
            if ruta_nueva == ultimo_viaje["ruta"]:
                messagebox.showwarning("Ruta inválida",
                                        "La ruta correcta debe ser diferente a la ruta ya abordada.")
                return

            viaje = {
                "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "ruta": ruta_nueva,
                "valor": 0,
                "codigo": f"{ultimo_viaje['codigo']}-TRASP",
                "metodo": f"Traspaso desde {ultimo_viaje['ruta']}",
            }
            self.historial_viajes.append(viaje)
            self._actualizar_header()
            ventana.destroy()
            self._mostrar_confirmacion(viaje, traspaso=True)

        self._boton_accion(ventana, "Confirmar traspaso", confirmar, self.COLOR_TRASPASO,
                             ancho=22).pack(pady=(16, 6))
        tk.Button(ventana, text="Cancelar", command=ventana.destroy, font=self.FUENTE_TEXTO_CHICA,
                   bg=self.COLOR_TARJETA, fg="#5B6B7C", relief="flat", cursor="hand2").pack()

    # ------------------------------------------------------------------
    # Recargar saldo
    # ------------------------------------------------------------------
    def recargar_saldo(self):
        self._marcar_boton_activo("recarga")
        ventana = self._crear_ventana_modal("Recargar saldo", 380, 420)

        tk.Label(ventana, text="RECARGAR SALDO", font=self.FUENTE_SUBTITULO,
                  bg=self.COLOR_TARJETA, fg=self.COLOR_TEXTO_OSCURO).pack(pady=(20, 4))
        tk.Label(ventana, text=f"Saldo actual: ${self.saldo_usuario:,}", font=self.FUENTE_TEXTO,
                  bg=self.COLOR_TARJETA, fg=self.COLOR_ACENTO_OSCURO).pack(pady=(0, 10))
        tk.Label(ventana, text="Seleccione el monto a recargar:", font=self.FUENTE_TEXTO_CHICA,
                  bg=self.COLOR_TARJETA, fg="#5B6B7C").pack()

        frame_montos = tk.Frame(ventana, bg=self.COLOR_TARJETA)
        frame_montos.pack(pady=12)

        montos = [10000, 20000, 50000, 100000]
        for i, monto in enumerate(montos):
            btn = tk.Button(frame_montos, text=f"${monto:,}", font=("Segoe UI", 10, "bold"),
                              bg="#E4E9F0", fg=self.COLOR_TEXTO_OSCURO, width=13, height=2,
                              relief="flat", cursor="hand2",
                              command=lambda m=monto: self._procesar_recarga(m, ventana))
            btn.grid(row=i // 2, column=i % 2, padx=6, pady=6)

        tk.Label(ventana, text="O ingrese un monto personalizado:", font=self.FUENTE_TEXTO_CHICA,
                  bg=self.COLOR_TARJETA, fg="#5B6B7C").pack(pady=(14, 4))

        self.entry_monto = tk.Entry(ventana, font=self.FUENTE_TEXTO, width=16, justify="center",
                                      relief="solid", bd=1)
        self.entry_monto.pack(pady=4)

        self._boton_accion(ventana, "Recargar monto personalizado",
                             lambda: self._procesar_recarga_personalizada(ventana),
                             self.COLOR_ACENTO, ancho=26).pack(pady=(14, 4))

    def _procesar_recarga(self, monto, ventana):
        self.saldo_usuario += monto
        self._actualizar_header()
        messagebox.showinfo("Recarga exitosa",
                              f"Recarga completada.\n\nMonto recargado: ${monto:,}\n"
                              f"Nuevo saldo: ${self.saldo_usuario:,}")
        ventana.destroy()

    def _procesar_recarga_personalizada(self, ventana):
        try:
            monto = int(self.entry_monto.get())
            if monto <= 0:
                messagebox.showerror("Monto inválido", "El monto debe ser mayor a cero.")
                return
            if monto > 500000:
                messagebox.showerror("Monto inválido", "El monto máximo de recarga es $500,000.")
                return
            self._procesar_recarga(monto, ventana)
        except ValueError:
            messagebox.showerror("Monto inválido", "Ingrese un número válido.")

    # ------------------------------------------------------------------
    # Confirmación genérica de pago
    # ------------------------------------------------------------------
    def _mostrar_confirmacion(self, viaje, traspaso=False):
        self._limpiar_contenido()
        self._titulo_seccion(self.frame_contenido, "Comprobante de viaje",
                              "El pago ha sido registrado correctamente")

        borde, panel = self._tarjeta(self.frame_contenido)
        borde.pack(fill="x")

        franja = tk.Frame(panel, bg=self.COLOR_ACENTO, height=5)
        franja.pack(fill="x")

        titulo = "TRASPASO CONFIRMADO" if traspaso else "PAGO CONFIRMADO"
        tk.Label(panel, text=titulo, font=("Segoe UI", 16, "bold"),
                  fg=self.COLOR_ACENTO_OSCURO, bg=self.COLOR_TARJETA).pack(pady=(18, 10))

        datos = [
            ("Ruta", viaje["ruta"]),
            ("Método de pago", viaje["metodo"]),
            ("Código de operación", viaje["codigo"]),
            ("Fecha y hora", viaje["fecha"]),
            ("Valor", "Sin costo adicional" if viaje["valor"] == 0 else f"${viaje['valor']:,}"),
        ]
        for etiqueta, valor in datos:
            fila = tk.Frame(panel, bg=self.COLOR_TARJETA)
            fila.pack(fill="x", padx=40, pady=3)
            tk.Label(fila, text=f"{etiqueta}:", font=self.FUENTE_TEXTO, fg="#5B6B7C",
                      bg=self.COLOR_TARJETA, width=20, anchor="w").pack(side="left")
            tk.Label(fila, text=valor, font=("Segoe UI", 10, "bold"), fg=self.COLOR_TEXTO_OSCURO,
                      bg=self.COLOR_TARJETA, anchor="w").pack(side="left")

        if not traspaso:
            tk.Label(panel, text=f"Saldo disponible tras la operación: ${self.saldo_usuario:,}",
                      font=self.FUENTE_TEXTO_CHICA, fg="#5B6B7C", bg=self.COLOR_TARJETA).pack(pady=(12, 0))

        tk.Label(panel, text="", bg=self.COLOR_TARJETA).pack(pady=10)

        self._boton_accion(self.frame_contenido, "Volver al panel principal", self.mostrar_inicio,
                             self.COLOR_ACENTO, ancho=26).pack(pady=20)

    # ------------------------------------------------------------------
    # Historial de viajes
    # ------------------------------------------------------------------
    def ver_historial(self):
        self._limpiar_contenido()
        self._marcar_boton_activo("historial")
        self._titulo_seccion(self.frame_contenido, "Historial de viajes",
                              "Registro de todos los pagos realizados en este terminal")

        if not self.historial_viajes:
            borde, panel = self._tarjeta(self.frame_contenido)
            borde.pack(fill="x", pady=10)
            tk.Label(panel, text="No hay viajes registrados todavía.", font=self.FUENTE_TEXTO,
                      fg="#5B6B7C", bg=self.COLOR_TARJETA).pack(pady=30)
            return

        borde_tabla, panel_tabla = self._tarjeta(self.frame_contenido)
        borde_tabla.pack(fill="both", expand=True)

        encabezados = tk.Frame(panel_tabla, bg=self.COLOR_FONDO_HEADER)
        encabezados.pack(fill="x")
        columnas = [("FECHA Y HORA", 18), ("RUTA", 10), ("MÉTODO DE PAGO", 18), ("CÓDIGO", 16), ("VALOR", 10)]
        for i, (nombre, ancho) in enumerate(columnas):
            tk.Label(encabezados, text=nombre, font=("Segoe UI", 9, "bold"), fg=self.COLOR_TEXTO_CLARO,
                      bg=self.COLOR_FONDO_HEADER, width=ancho, anchor="w").grid(row=0, column=i, padx=6, pady=8)

        canvas = tk.Canvas(panel_tabla, bg=self.COLOR_TARJETA, highlightthickness=0)
        scrollbar = tk.Scrollbar(panel_tabla, orient="vertical", command=canvas.yview)
        marco_scroll = tk.Frame(canvas, bg=self.COLOR_TARJETA)

        marco_scroll.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=marco_scroll, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        for i, viaje in enumerate(reversed(self.historial_viajes)):
            color_fila = "#F7F9FB" if i % 2 == 0 else self.COLOR_TARJETA
            fila = tk.Frame(marco_scroll, bg=color_fila)
            fila.pack(fill="x")
            valor_texto = "Sin costo" if viaje["valor"] == 0 else f"${viaje['valor']:,}"
            tk.Label(fila, text=viaje["fecha"], font=self.FUENTE_TEXTO_CHICA, bg=color_fila,
                      fg=self.COLOR_TEXTO_OSCURO, width=18, anchor="w").grid(row=0, column=0, padx=6, pady=5)
            tk.Label(fila, text=viaje["ruta"], font=self.FUENTE_TEXTO_CHICA, bg=color_fila,
                      fg=self.COLOR_TEXTO_OSCURO, width=10, anchor="w").grid(row=0, column=1, padx=6)
            tk.Label(fila, text=viaje["metodo"], font=self.FUENTE_TEXTO_CHICA, bg=color_fila,
                      fg=self.COLOR_TEXTO_OSCURO, width=18, anchor="w").grid(row=0, column=2, padx=6)
            tk.Label(fila, text=viaje["codigo"], font=self.FUENTE_TEXTO_CHICA, bg=color_fila,
                      fg=self.COLOR_TEXTO_OSCURO, width=16, anchor="w").grid(row=0, column=3, padx=6)
            tk.Label(fila, text=valor_texto, font=self.FUENTE_TEXTO_CHICA, bg=color_fila,
                      fg=self.COLOR_TEXTO_OSCURO, width=10, anchor="w").grid(row=0, column=4, padx=6)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Resumen estadístico por método de pago
        borde_resumen, panel_resumen = self._tarjeta(self.frame_contenido)
        borde_resumen.pack(fill="x", pady=(14, 0))

        total_gastado = sum(v["valor"] for v in self.historial_viajes)
        total_por_metodo = {}
        for v in self.historial_viajes:
            total_por_metodo[v["metodo"]] = total_por_metodo.get(v["metodo"], 0) + v["valor"]

        tk.Label(panel_resumen, text="Resumen de recaudo", font=self.FUENTE_SUBTITULO,
                  fg=self.COLOR_TEXTO_OSCURO, bg=self.COLOR_TARJETA).pack(anchor="w", padx=18, pady=(12, 6))

        tk.Label(panel_resumen, text=f"Total de viajes registrados: {len(self.historial_viajes)}    "
                                       f"Total recaudado: ${total_gastado:,}",
                  font=self.FUENTE_TEXTO_CHICA, fg="#3D4A57", bg=self.COLOR_TARJETA).pack(anchor="w", padx=18)

        for metodo, valor in total_por_metodo.items():
            tk.Label(panel_resumen, text=f"  {metodo}: ${valor:,}", font=self.FUENTE_TEXTO_CHICA,
                      fg="#3D4A57", bg=self.COLOR_TARJETA).pack(anchor="w", padx=18, pady=1)

        tk.Label(panel_resumen, text="", bg=self.COLOR_TARJETA).pack(pady=6)

    # ------------------------------------------------------------------
    def ejecutar(self):
        self.ventana.mainloop()


if __name__ == "__main__":
    print("Iniciando Sistema de Recaudo Electronico - Transporte Publico Ibague")
    print("Cargando modulos de interfaz...")
    print("Sistema listo.")

    app = SistemaPagoQR()
    app.ejecutar()
    

    app = SistemaPagoQR()
    app.ejecutar()
