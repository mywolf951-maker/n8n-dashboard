import customtkinter as ctk
from PIL import Image, ImageTk # Importar ImageTk para compatibilidad con CTkImage
import os
import sys
import time
import pyperclip
import requests
import tkinter as tk # Importar tkinter para filedialog
import threading # Necesario para operaciones en segundo plano

# Importar las clases y funciones modularizadas
from usuario_config import ConfigUsuario
from language_manager import LanguageManager
from logger_dashboard import LoggerDashboard
from servicios import Servicios
from recursos import Recursos # Para rutas de iconos y logos

class App(ctk.CTk):
    """
    Clase principal de la aplicación GUI para controlar n8n, ngrok y MailHog.
    """
    def __init__(self):
        super().__init__()

        # 1. Inicializar el logger lo antes posible
        # Se inicializa sin lang_manager al principio para evitar dependencia circular.
        # Se actualizará después de cargar la configuración y el idioma.
        self.logger_dashboard = LoggerDashboard(app_instance=self)
        self.logger_dashboard.log("INFO", "log_app_starting")

        # 2. Cargar configuración de usuario
        self.config = ConfigUsuario()
        
        # 3. Inicializar el gestor de idiomas con el idioma de la configuración
        idioma_preferido = self.config.get("idioma", "es")
        self.lang = LanguageManager(idioma_preferido)
        # Actualizar el logger con el gestor de idiomas
        self.logger_dashboard.lang = self.lang

        # 4. Inicializar la clase de servicios
        self.servicios = Servicios(self.logger_dashboard, self.lang, self.config)

        # Configuración de la ventana principal
        self.title(self.lang.get("app_title"))
        self.geometry("460x750") # Aumentar la altura para el panel de logs
        self.resizable(False, False) # Hacer la ventana no redimensionable

        # Configuración del icono de la aplicación
        try:
            icon_path = Recursos.icono()
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
                self.logger_dashboard.log("INFO", "log_icon_loaded")
            else:
                self.logger_dashboard.log("ERROR", "log_icon_error", f"Icon file not found at {icon_path}")
        except Exception as e:
            self.logger_dashboard.log("ERROR", "log_icon_error", str(e))

        # Configuración del logo principal
        try:
            logo_image_path = Recursos.logo()
            if os.path.exists(logo_image_path):
                logo_image = ctk.CTkImage(Image.open(logo_image_path), size=(420, 120))
                ctk.CTkLabel(self, image=logo_image, text="").pack(pady=(20, 10))
                self.logger_dashboard.log("INFO", "log_logo_loaded")
            else:
                self.logger_dashboard.log("ERROR", "log_logo_error", f"Logo file not found at {logo_image_path}")
        except Exception as e:
            self.logger_dashboard.log("ERROR", "log_logo_error", str(e))

        # Configurar el protocolo de cierre de ventana
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Crear las pestañas
        self.tabview = ctk.CTkTabview(self, width=420)
        self.tabview.pack(pady=10, padx=20, fill="both", expand=True)

        self.tabview.add(self.lang.get("tab_control"))
        self.tabview.add(self.lang.get("tab_settings"))

        # Inicializar las listas de botones para evitar NameError
        self.n8n_buttons = []
        self.ngrok_buttons = []
        self.mailhog_buttons = []

        # Construir la UI de la pestaña de Control
        self._build_control_tab()
        # Construir la UI de la pestaña de Configuración
        self._build_settings_tab()

        # --- Panel Visual de Logs ---
        self.log_frame = ctk.CTkFrame(self)
        self.log_frame.pack(pady=10, padx=20, fill="both", expand=True)

        ctk.CTkLabel(self.log_frame, text=self.lang.get("log_panel_title"), font=("Arial", 16, "bold")).pack(pady=(5, 0))

        self.log_textbox = ctk.CTkTextbox(self.log_frame, width=400, height=150, wrap="word")
        self.log_textbox.pack(pady=5, padx=5, fill="both", expand=True)
        self.log_textbox.configure(state="disabled") # Hacer el textbox de solo lectura

        # Conectar el textbox al logger
        self.logger_dashboard.set_log_textbox(self.log_textbox)

        # Botón para limpiar los logs
        ctk.CTkButton(self.log_frame, text=self.lang.get("clear_logs_button"), command=self._clear_log_panel, width=150).pack(pady=(0, 5))

        # Inicializar y actualizar el estado de los servicios
        self._update_service_status_periodically()

    def _clear_log_panel(self):
        """Limpia el contenido del panel de logs visual."""
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")
        self.logger_dashboard.log("INFO", "log_panel_cleared") # Registrar que el panel fue limpiado

    def _build_control_tab(self):
        """Construye la interfaz de usuario para la pestaña de Control."""
        # Sección de n8n
        frame_n8n = ctk.CTkFrame(self.tabview.tab(self.lang.get("tab_control")))
        frame_n8n.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(frame_n8n, text=self.lang.get("n8n_control_section_title"), font=("Arial", 16, "bold")).pack(pady=10)
        btn_iniciar_n8n = ctk.CTkButton(frame_n8n, text=self.lang.get("n8n_button_start"), command=self._iniciar_n8n_wrapper, width=300)
        btn_iniciar_n8n.pack(pady=5)
        btn_detener_n8n = ctk.CTkButton(frame_n8n, text=self.lang.get("n8n_button_stop"), command=self._detener_n8n_wrapper, width=300)
        btn_detener_n8n.pack(pady=5)
        btn_reiniciar_n8n = ctk.CTkButton(frame_n8n, text=self.lang.get("n8n_button_restart"), command=self._reiniciar_n8n_wrapper, width=300)
        btn_reiniciar_n8n.pack(pady=5)
        self.n8n_buttons = [btn_iniciar_n8n, btn_detener_n8n, btn_reiniciar_n8n] # Asignar a la lista
        self.n8n_status_label = ctk.CTkLabel(frame_n8n, text=self.lang.get("n8n_status_unknown"), font=("Arial", 12))
        self.n8n_status_label.pack(pady=5)

        # Sección de ngrok
        frame_ngrok = ctk.CTkFrame(self.tabview.tab(self.lang.get("tab_control")))
        frame_ngrok.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(frame_ngrok, text=self.lang.get("ngrok_control_section_title"), font=("Arial", 16, "bold")).pack(pady=10)
        btn_iniciar_ngrok = ctk.CTkButton(frame_ngrok, text=self.lang.get("ngrok_button_start_copy"), command=self._iniciar_ngrok_wrapper, width=300)
        btn_iniciar_ngrok.pack(pady=5)
        btn_detener_ngrok = ctk.CTkButton(frame_ngrok, text=self.lang.get("ngrok_button_stop"), command=self._detener_ngrok_wrapper, width=300)
        btn_detener_ngrok.pack(pady=5)
        self.ngrok_buttons = [btn_iniciar_ngrok, btn_detener_ngrok] # Asignar a la lista
        self.ngrok_status_label = ctk.CTkLabel(frame_ngrok, text=self.lang.get("ngrok_status_unknown"), font=("Arial", 12))
        self.ngrok_status_label.pack(pady=5)

        # Sección de MailHog
        frame_mailhog = ctk.CTkFrame(self.tabview.tab(self.lang.get("tab_control")))
        frame_mailhog.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(frame_mailhog, text=self.lang.get("mailhog_control_section_title"), font=("Arial", 16, "bold")).pack(pady=10)
        btn_iniciar_mailhog = ctk.CTkButton(frame_mailhog, text=self.lang.get("mailhog_button_start"), command=self._iniciar_mailhog_wrapper, width=300)
        btn_iniciar_mailhog.pack(pady=5)
        btn_detener_mailhog = ctk.CTkButton(frame_mailhog, text=self.lang.get("mailhog_button_stop"), command=self._detener_mailhog_wrapper, width=300)
        btn_detener_mailhog.pack(pady=5)
        self.mailhog_buttons = [btn_iniciar_mailhog, btn_detener_mailhog] # Asignar a la lista
        self.mailhog_status_label = ctk.CTkLabel(frame_mailhog, text=self.lang.get("mailhog_status_unknown"), font=("Arial", 12))
        self.mailhog_status_label.pack(pady=5)


        # Sección de estado general de servicios (opcional, si quieres un resumen)
        frame_status = ctk.CTkFrame(self.tabview.tab(self.lang.get("tab_control")))
        frame_status.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(frame_status, text=self.lang.get("services_status_section_title"), font=("Arial", 16, "bold")).pack(pady=10)
        self.general_status_label = ctk.CTkLabel(frame_status, text="", font=("Arial", 12), text_color="gray")
        self.general_status_label.pack(pady=5)
        
        # Botón de Salir
        ctk.CTkButton(self.tabview.tab(self.lang.get("tab_control")), text=self.lang.get("button_exit"), command=self.salir_app, width=300, fg_color="red", hover_color="darkred").pack(pady=20)


    def _build_settings_tab(self):
        """Construye la interfaz de usuario para la pestaña de Configuración."""
        settings_frame = ctk.CTkFrame(self.tabview.tab(self.lang.get("tab_settings")))
        settings_frame.pack(pady=10, padx=10, fill="both", expand=True)

        ctk.CTkLabel(settings_frame, text=self.lang.get("settings_title"), font=("Arial", 16, "bold")).pack(pady=10)

        # n8n Installation Path
        ctk.CTkLabel(settings_frame, text=self.lang.get("n8n_install_path_label")).pack(pady=(10,0))
        self.n8n_path_entry = ctk.CTkEntry(settings_frame, width=300)
        self.n8n_path_entry.insert(0, self.config.get_nested("servicios", "n8n", "ruta_instalacion", default=""))
        self.n8n_path_entry.pack(pady=5)
        ctk.CTkButton(settings_frame, text=self.lang.get("browse_button"), command=self._browse_n8n_path).pack(pady=5)

        # ngrok Executable Path
        ctk.CTkLabel(settings_frame, text=self.lang.get("ngrok_exec_path_label")).pack(pady=(10,0))
        self.ngrok_path_entry = ctk.CTkEntry(settings_frame, width=300)
        self.ngrok_path_entry.insert(0, self.config.get_nested("servicios", "ngrok", "ruta_ejecutable", default=""))
        self.ngrok_path_entry.pack(pady=5)
        ctk.CTkButton(settings_frame, text=self.lang.get("browse_button"), command=self._browse_ngrok_path).pack(pady=5)

        # MailHog Executable Path
        ctk.CTkLabel(settings_frame, text=self.lang.get("mailhog_exec_path_label")).pack(pady=(10,0))
        self.mailhog_path_entry = ctk.CTkEntry(settings_frame, width=300)
        self.mailhog_path_entry.insert(0, self.config.get_nested("servicios", "mailhog", "ruta_ejecutable", default=""))
        self.mailhog_path_entry.pack(pady=5)
        ctk.CTkButton(settings_frame, text=self.lang.get("browse_button"), command=self._browse_mailhog_path).pack(pady=5)

        # ngrok Auth Token
        ctk.CTkLabel(settings_frame, text=self.lang.get("ngrok_authtoken_label")).pack(pady=(10,0))
        self.ngrok_authtoken_entry = ctk.CTkEntry(settings_frame, width=300, show="*") # Show * for password field
        self.ngrok_authtoken_entry.insert(0, self.config.get_nested("servicios", "ngrok", "authtoken", default=""))
        self.ngrok_authtoken_entry.pack(pady=5)

        # Save Settings Button
        ctk.CTkButton(settings_frame, text=self.lang.get("save_settings_button"), command=self._save_settings, width=300).pack(pady=20)

    def _browse_n8n_path(self):
        folder_selected = tk.filedialog.askdirectory(title=self.lang.get("select_n8n_path_title"))
        if folder_selected:
            self.n8n_path_entry.delete(0, ctk.END)
            self.n8n_path_entry.insert(0, folder_selected)
            # Log the path update
            self.logger_dashboard.log("INFO", "log_n8n_path_updated", folder_selected)

    def _browse_ngrok_path(self):
        file_selected = tk.filedialog.askopenfilename(title=self.lang.get("select_ngrok_exec_title"), filetypes=[("Executable files", "*.exe")])
        if file_selected:
            # Almacenar solo el directorio si el usuario selecciona el archivo directamente
            directory_selected = os.path.dirname(file_selected)
            self.ngrok_path_entry.delete(0, ctk.END)
            self.ngrok_path_entry.insert(0, directory_selected)
            # Log the path update
            self.logger_dashboard.log("INFO", "log_ngrok_path_updated", directory_selected)

    def _browse_mailhog_path(self):
        # Para MailHog, el usuario selecciona la CARPETA donde está MailHog_windows_amd64.exe
        folder_selected = tk.filedialog.askdirectory(title=self.lang.get("select_mailhog_exec_title"))
        if folder_selected:
            self.mailhog_path_entry.delete(0, ctk.END)
            self.mailhog_path_entry.insert(0, folder_selected)

    def _save_settings(self):
        # Guardar rutas y authtoken
        self.config.set_nested("servicios", "n8n", "ruta_instalacion", self.n8n_path_entry.get())
        self.config.set_nested("servicios", "ngrok", "ruta_ejecutable", self.ngrok_path_entry.get())
        self.config.set_nested("servicios", "mailhog", "ruta_ejecutable", self.mailhog_path_entry.get())
        self.config.set_nested("servicios", "ngrok", "authtoken", self.ngrok_authtoken_entry.get())
        
        # Guardar los cambios en el archivo
        self.config._save_preferences() # Llamada explícita para guardar

        self.logger_dashboard.log("INFO", "settings_saved")
        self.general_status_label.configure(text=self.lang.get("settings_saved"), text_color="green")

    # --- Métodos de Gestión de Fondo y Preferencias ---
    # Los métodos de fondo (cargar_preferencia, guardar_preferencia, cambiar_modo, on_resize, actualizar_fondo, fade_in)
    # se mantienen como estaban, ya que no fueron parte de los cambios solicitados por ChatGPT para el panel de logs.
    # Asegúrate de que estos métodos están presentes en tu app.py si los necesitas.
    def cargar_preferencia(self):
        return self.config.get("modo_fondo", self.lang.get("background_mode_fullscreen"))

    def guardar_preferencia(self, modo):
        self.config.set("modo_fondo", modo)

    def cambiar_modo(self, nuevo_modo):
        self.guardar_preferencia(nuevo_modo)
        self.actualizar_fondo()

    def on_resize(self, event):
        if event.widget == self and (self.winfo_width() > 1 and self.winfo_height() > 1):
            self.actualizar_fondo()

    def actualizar_fondo(self):
        modo = self.modo_fondo.get()
        ancho, alto = self.winfo_width(), self.winfo_height()
        if ancho == 1 and alto == 1:
            self.after(50, self.actualizar_fondo)
            return

        try:
            logo = Image.open(Recursos.logo()).convert("RGBA")
        except Exception as e:
            self.logger_dashboard.log("ERROR", "log_background_image_error", str(e))
            return

        if modo == self.lang.get("background_mode_fullscreen"):
            fondo_img = logo.resize((ancho, alto), Image.LANCZOS)
        else:
            fondo_img = Image.new("RGBA", (ancho, alto))
            for x in range(0, ancho, logo.width):
                for y in range(0, alto, logo.height):
                    fondo_img.paste(logo, (x, y))

        # Aplicar desenfoque y superposición (si ImageFilter está importado)
        # Asegúrate de que ImageFilter y ImageEnhance estén importados desde PIL si usas esto.
        # from PIL import Image, ImageGrab, ImageTk, ImageFilter, ImageEnhance
        try:
            from PIL import ImageFilter
            fondo_img = fondo_img.filter(ImageFilter.GaussianBlur(radius=3))
            overlay = Image.new("RGBA", fondo_img.size, (0, 0, 0, 100))
            fondo_img = Image.alpha_composite(fondo_img, overlay)
        except ImportError:
            self.logger_dashboard.log("WARNING", "image_filter_not_available") # Nueva clave de traducción
        except Exception as e:
            self.logger_dashboard.log("ERROR", "background_filter_error", str(e)) # Nueva clave de traducción


        fondo_ctk_img = ctk.CTkImage(light_image=fondo_img, size=(ancho, alto))

        if hasattr(self, "fondo_label"):
            self.fondo_label.configure(image=fondo_ctk_img)
            self.fondo_label.image = fondo_ctk_img
        else:
            self.fondo_label = ctk.CTkLabel(self, image=fondo_ctk_img, text="")
            self.fondo_label.place(relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=1)
            self.fondo_label.lower()
            self.fondo_label.image = fondo_ctk_img

        self.logger_dashboard.log("INFO", "log_background_updated", modo)

    # El método fade_in no es estrictamente necesario para la funcionalidad básica de fondo,
    # pero si lo quieres mantener para transiciones, asegúrate de que esté bien implementado.
    # Por simplicidad, lo he omitido en esta versión para centrarme en las funcionalidades principales.
    # Si lo necesitas, podemos reincorporarlo.

    # --- Métodos de Control de n8n (Delegados a Servicios) ---
    def _set_n8n_buttons_state(self, state):
        for button in self.n8n_buttons:
            button.configure(state=state)

    def _iniciar_n8n_wrapper(self):
        self._set_n8n_buttons_state("disabled")
        self.general_status_label.configure(text=self.lang.get("log_n8n_starting"), text_color="orange")
        threading.Thread(target=self._run_n8n_operation, args=(self.servicios.iniciar_n8n, "n8n_started_message", "n8n_start_failed_message", self._set_n8n_buttons_state)).start()

    def _detener_n8n_wrapper(self):
        self._set_n8n_buttons_state("disabled")
        self.general_status_label.configure(text=self.lang.get("log_n8n_stopping"), text_color="orange")
        threading.Thread(target=self._run_n8n_operation, args=(self.servicios.detener_n8n, "n8n_stopped_message", "n8n_stop_failed_message", self._set_n8n_buttons_state)).start()

    def _reiniciar_n8n_wrapper(self):
        self._set_n8n_buttons_state("disabled")
        self.general_status_label.configure(text=self.lang.get("log_n8n_restarting"), text_color="orange")
        threading.Thread(target=self._run_n8n_operation, args=(self.servicios.reiniciar_n8n, "n8n_restarted_message", "n8n_restart_failed_message", self._set_n8n_buttons_state)).start()

    def _run_n8n_operation(self, service_method, success_key, fail_key, button_setter_func):
        exito, mensaje = service_method()
        self.after(0, lambda: self._update_gui_after_operation(exito, mensaje, success_key, fail_key, button_setter_func))
        self.after(5000, self._update_service_status_periodically) # Re-verificar estado después de operación

    # --- Métodos de Control de ngrok (Delegados a Servicios) ---
    def _set_ngrok_buttons_state(self, state):
        for button in self.ngrok_buttons:
            button.configure(state=state)

    def _iniciar_ngrok_wrapper(self):
        self._set_ngrok_buttons_state("disabled")
        self.general_status_label.configure(text=self.lang.get("log_ngrok_starting"), text_color="orange")
        threading.Thread(target=self._run_ngrok_operation, args=(self.servicios.iniciar_ngrok, "ngrok_active_message", "ngrok_start_failed_message", self._set_ngrok_buttons_state)).start()

    def _detener_ngrok_wrapper(self):
        self._set_ngrok_buttons_state("disabled")
        self.general_status_label.configure(text=self.lang.get("log_ngrok_stopping"), text_color="orange")
        threading.Thread(target=self._run_ngrok_operation, args=(self.servicios.detener_ngrok, "ngrok_stopped_message", "ngrok_stop_failed_message", self._set_ngrok_buttons_state)).start()

    def _run_ngrok_operation(self, service_method, success_key, fail_key, button_setter_func):
        exito, mensaje = service_method()
        self.after(0, lambda: self._update_gui_after_operation(exito, mensaje, success_key, fail_key, button_setter_func))
        self.after(5000, self._update_service_status_periodically) # Re-verificar estado después de operación

    # --- Métodos de Control de MailHog (Delegados a Servicios) ---
    def _set_mailhog_buttons_state(self, state):
        for button in self.mailhog_buttons:
            button.configure(state=state)

    def _iniciar_mailhog_wrapper(self):
        self._set_mailhog_buttons_state("disabled")
        self.general_status_label.configure(text=self.lang.get("log_mailhog_starting"), text_color="orange")
        threading.Thread(target=self._run_mailhog_operation, args=(self.servicios.iniciar_mailhog, "mailhog_started_message", "mailhog_start_failed_message", self._set_mailhog_buttons_state)).start()

    def _detener_mailhog_wrapper(self):
        self._set_mailhog_buttons_state("disabled")
        self.general_status_label.configure(text=self.lang.get("log_mailhog_stopping"), text_color="orange")
        threading.Thread(target=self._run_mailhog_operation, args=(self.servicios.detener_mailhog, "mailhog_stopped_message", "mailhog_stop_failed_message", self._set_mailhog_buttons_state)).start()

    def _run_mailhog_operation(self, service_method, success_key, fail_key, button_setter_func):
        exito, mensaje = service_method()
        self.after(0, lambda: self._update_gui_after_operation(exito, mensaje, success_key, fail_key, button_setter_func))
        self.after(5000, self._update_service_status_periodically) # Re-verificar estado después de operación

    def _update_gui_after_operation(self, exito, message, success_key, fail_key, button_setter_func):
        """
        Actualiza la etiqueta de estado general de la GUI después de una operación de servicio.
        'message' ya debe ser el texto traducido o el error en crudo.
        """
        if exito:
            # Si es ngrok, el mensaje ya viene formateado con la URL
            if success_key == "ngrok_active_message":
                self.general_status_label.configure(text=self.lang.get(success_key, message), text_color="green")
            else:
                # Para otros servicios, el mensaje ya es el texto traducido de éxito
                self.general_status_label.configure(text=self.lang.get(success_key), text_color="green")
        else:
            # Para fallos, el mensaje ya es el texto traducido de fallo o el error en crudo
            self.general_status_label.configure(text=self.lang.get(fail_key, message), text_color="red")
        
        button_setter_func("normal") # Asegurarse de re-habilitar los botones


    # --- Métodos de Estado de Servicios ---
    def _update_mailhog_status_wrapper(self):
        """Wrapper para actualizar el estado de MailHog manualmente."""
        threading.Thread(target=self._run_mailhog_status_check).start()

    def _run_mailhog_status_check(self):
        """Verifica el estado de MailHog y actualiza la UI."""
        mailhog_status_key, *mailhog_args = self.servicios.check_mailhog_status()
        mailhog_status_msg = self.lang.get(mailhog_status_key, *mailhog_args)
        self.after(0, lambda: self.mailhog_status_label.configure(text=f"MailHog: {mailhog_status_msg}", text_color="green" if "active" in mailhog_status_key else "red"))
        self.logger_dashboard.log("INFO", "log_mailhog_verification", mailhog_status_msg)


    def _update_service_status_periodically(self):
        """Verifica el estado de todos los servicios y actualiza sus etiquetas."""
        # Se ejecuta en un hilo para no bloquear la UI
        threading.Thread(target=self._run_all_service_checks).start()
        # Vuelve a programar la verificación periódica
        self.after(5000, self._update_service_status_periodically) # Actualizar cada 5 segundos

    def _run_all_service_checks(self):
        """Lógica para verificar el estado de cada servicio."""
        # n8n Status
        n8n_status_key, *n8n_args = self.servicios.check_n8n_status()
        n8n_status_msg = self.lang.get(n8n_status_key, *n8n_args)
        self.after(0, lambda: self.n8n_status_label.configure(text=n8n_status_msg, text_color="green" if "active" in n8n_status_key else "red"))

        # ngrok Status
        ngrok_status_key, *ngrok_args = self.servicios.check_ngrok_status()
        ngrok_status_msg = self.lang.get(ngrok_status_key, *ngrok_args)
        self.after(0, lambda: self.ngrok_status_label.configure(text=ngrok_status_msg, text_color="green" if "active" in ngrok_status_key else "red"))

        # MailHog Status
        mailhog_status_key, *mailhog_args = self.servicios.check_mailhog_status()
        mailhog_status_msg = self.lang.get(mailhog_status_key, *mailhog_args)
        self.after(0, lambda: self.mailhog_status_label.configure(text=f"MailHog: {mailhog_status_msg}", text_color="green" if "active" in mailhog_status_key else "red"))
        
        self.logger_dashboard.log("INFO", "log_service_status_updated")


    # --- Método para Salir de la Aplicación ---
    def on_closing(self):
        """Maneja el cierre de la ventana, deteniendo los servicios."""
        self.logger_dashboard.log("INFO", "app_closing_message")
        self.general_status_label.configure(text=self.lang.get("app_closing_message"), text_color="blue")

        # Deshabilitar el botón de salir para evitar múltiples clics
        # self.btn_salir.configure(state="disabled") # Este botón no existe en la estructura actual

        # Iniciar el proceso de detención de servicios en un hilo separado
        threading.Thread(target=self._stop_services_on_exit_thread).start()

    def _stop_services_on_exit_thread(self):
        """Detiene todos los servicios en un hilo separado."""
        # Detener n8n
        stop_n8n_success, stop_n8n_msg = self.servicios.detener_n8n()
        self.logger_dashboard.log("INFO" if stop_n8n_success else "ERROR", "n8n_stopped_on_exit" if stop_n8n_success else "n8n_stop_failed_on_exit", stop_n8n_msg)

        # Detener ngrok
        stop_ngrok_success, stop_ngrok_msg = self.servicios.detener_ngrok()
        self.logger_dashboard.log("INFO" if stop_ngrok_success else "ERROR", "ngrok_stopped_on_exit" if stop_ngrok_success else "ngrok_stop_failed_on_exit", stop_ngrok_msg)

        # Detener MailHog
        stop_mailhog_success, stop_mailhog_msg = self.servicios.detener_mailhog()
        self.logger_dashboard.log("INFO" if stop_mailhog_success else "ERROR", "mailhog_stopped_on_exit" if stop_mailhog_success else "mailhog_stop_failed_on_exit", stop_mailhog_msg)
        
        # Después de intentar detener todos los servicios, cerrar la aplicación en el hilo principal
        self.after(0, self.destroy)

    def salir_app(self):
        self.on_closing()
