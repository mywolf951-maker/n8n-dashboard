import logging
import sys
# Importar funciones de utilidad. No importar customtkinter aquí para evitar dependencias circulares.
from utils import capturar_widget, enviar_a_mailhog

class LoggerDashboard:
    """
    Gestiona el registro de eventos de la aplicación,
    incluyendo salida a archivo, consola, panel de logs en GUI, y alertas críticas.
    """
    def __init__(self, app_instance=None, lang_manager=None):
        self.logger = logging.getLogger("Dashboard")
        self.logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

        # Handler para archivo de log
        file_handler = logging.FileHandler("actividad_log.txt", encoding="utf-8")
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Handler para consola (StreamHandler)
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        self.logger.addHandler(stream_handler)

        self.app = app_instance
        self.lang = lang_manager
        self.log_textbox = None  # Widget TextBox para mostrar logs en la GUI

    def set_log_textbox(self, textbox_widget):
        """
        Conecta un widget TextBox para mostrar los mensajes de log en tiempo real.
        """
        self.log_textbox = textbox_widget

    def log(self, nivel, mensaje_clave, *args):
        """
        Registra un mensaje con el nivel especificado.
        Además de escribirlo en archivo/consola, puede mostrarse en un panel GUI si está conectado.
        """
        mensaje_traducido = self.lang.get(mensaje_clave, *args) if self.lang else mensaje_clave

        # Registro tradicional
        if nivel == "INFO":
            self.logger.info(mensaje_traducido)
        elif nivel == "WARNING":
            self.logger.warning(mensaje_traducido)
        elif nivel == "ERROR":
            self.logger.error(mensaje_traducido)
        elif nivel == "CRITICAL":
            self.logger.critical(mensaje_traducido)
            self.mostrar_popup_critico(mensaje_traducido)

            if self.app:
                exito, msg_or_path = capturar_widget(self.app)
                if exito:
                    ruta = msg_or_path
                    subject = self.lang.get("popup_critical_title")
                    content = self.lang.get("popup_critical_message")
                    enviado, estado_key_or_error = enviar_a_mailhog(ruta, subject, content)
                    if enviado:
                        self.logger.info(self.lang.get("log_capture_sent", self.lang.get(estado_key_or_error)))
                    else:
                        self.logger.error(self.lang.get("mailhog_send_error", estado_key_or_error))
                else:
                    self.logger.warning(self.lang.get("log_capture_failed", msg_or_path))

        # Mostrar en el panel de logs si está conectado
        if self.log_textbox:
            try:
                self.log_textbox.insert("end", f"[{nivel}] {mensaje_traducido}\n")
                self.log_textbox.see("end")
            except Exception as e:
                self.logger.warning(f"Error al escribir en el panel de logs: {e}")

    def mostrar_popup_critico(self, mensaje):
        """
        Muestra una ventana emergente (popup) para notificar un evento crítico.
        """
        import customtkinter as ctk

        if self.app:
            popup = ctk.CTkToplevel(self.app)
            popup.title(self.lang.get("popup_critical_title"))
            popup.geometry("400x120")

            # Centrar el popup en la pantalla principal
            app_x = self.app.winfo_x()
            app_y = self.app.winfo_y()
            app_width = self.app.winfo_width()
            app_height = self.app.winfo_height()

            popup_width = 400
            popup_height = 120

            x_pos = app_x + (app_width // 2) - (popup_width // 2)
            y_pos = app_y + (app_height // 2) - (popup_height // 2)

            popup.geometry(f"{popup_width}x{popup_height}+{x_pos}+{y_pos}")

            ctk.CTkLabel(popup, text=self.lang.get("popup_critical_message"), font=("Arial", 14, "bold")).pack(pady=(15, 5))
            ctk.CTkLabel(popup, text=mensaje, font=("Arial", 12)).pack()
            popup.attributes("-topmost", True)
            popup.after(5000, popup.destroy)
