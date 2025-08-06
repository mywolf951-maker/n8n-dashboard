import tkinter as tk
from tkinter import PhotoImage
from launcher import Launcher
from logger_dashboard import LoggerDashboard
from servicios import Servicios
from recursos import Recursos
from utils import centrar_ventana


class App(tk.Tk):
    def __init__(self, lang, config):
        super().__init__()
        self.lang = lang
        self.config = config

        # Configurar ventana principal
        self.title("Control Central n8n")
        self.iconbitmap(Recursos.icono())
        self.configure(bg="#1e1e1e")
        self.geometry("800x600")
        centrar_ventana(self)
        self.resizable(False, False)

        # Crear logger
        self.logger = LoggerDashboard(self)
        self.logger.pack(pady=10)

        # Crear servicios (pasando lang y config como requiere ahora)
        self.servicios = Servicios(self.lang, self.config)

        # Crear panel de botones
        self.panel_botones = tk.Frame(self, bg="#1e1e1e")
        self.panel_botones.pack(pady=20)

        self.crear_botones_servicios()

        # Crear logo
        self.logo_path = Recursos.logo()
        self.logo_img = PhotoImage(file=self.logo_path)
        self.logo_label = tk.Label(self, image=self.logo_img, bg="#1e1e1e")
        self.logo_label.pack(side="bottom", pady=10)

        # Log inicial
        self.logger.escribir_log("log_app_starting", "info")

    def crear_botones_servicios(self):
        servicios = ["n8n", "ngrok", "MailHog"]
        for servicio in servicios:
            boton = tk.Button(
                self.panel_botones,
                text=self.lang.get(f"iniciar_{servicio}", f"Iniciar {servicio}"),
                width=20,
                bg="#0078D7",
                fg="white",
                font=("Segoe UI", 10, "bold"),
                command=lambda s=servicio: self.iniciar_servicio(s)
            )
            boton.pack(pady=5)

    def iniciar_servicio(self, servicio):
        self.logger.escribir_log(f"Intentando iniciar {servicio}...", "info")
        resultado = self.servicios.lanzar(servicio)
        self.logger.escribir_log(resultado["mensaje"], resultado["nivel"])
