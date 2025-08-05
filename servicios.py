import subprocess
import time
import requests
import pyperclip
import os
import json
import sys
import socket
import logging # Asegurarse de que logging esté importado si se usa directamente aquí

class Servicios:
    """
    Clase que encapsula la lógica para iniciar, detener y reiniciar
    los servicios de n8n y ngrok.
    """
    # Constantes para nombres de servicios y puertos
    N8N_PM2_NAME = "n8n" # Se mantiene por si se decide volver a PM2, pero no se usa directamente ahora
    N8N_WEB_PORT = 5678 # Puerto por defecto de n8n
    NGROK_API_URL = "http://localhost:4040/api/tunnels"
    NGROK_API_TIMEOUT_INITIAL = 5 # Tiempo de espera inicial para la API de ngrok
    NGROK_API_RETRIES = 10 # Número de reintentos para conectar a la API de ngrok
    NGROK_API_RETRY_DELAY = 1 # Retraso entre reintentos (segundos)
    PM2_CHECK_TIMEOUT = 10 # Aumentado el timeout para la verificación de pm2

    # Puertos de MailHog
    MAILHOG_WEB_PORT = 8025
    MAILHOG_SMTP_PORT = 1025
    MAILHOG_API_RETRIES = 10 # Número de reintentos para conectar a MailHog
    MAILHOG_RETRY_DELAY = 1 # Retraso entre reintentos (segundos)


    def __init__(self, logger_dashboard, lang_manager, config):
        self.logger_dashboard = logger_dashboard
        self.lang = lang_manager
        self.config = config
        # Almacenar procesos para poder terminarlos
        self.n8n_process = None
        self.ngrok_process = None
        self.mailhog_process = None

    def _puerto_activo(self, puerto):
        """Verifica si el puerto está en uso en localhost."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.settimeout(0.1) # Pequeño timeout para no bloquear
                return s.connect_ex(('localhost', puerto)) == 0
            except Exception:
                return False

    def _get_ngrok_authtoken(self):
        """Obtiene el authtoken de ngrok desde la configuración de usuario."""
        return self.config.get_nested("servicios", "ngrok", "authtoken", default="")

    def _get_n8n_command_path(self):
        """
        Obtiene la ruta al ejecutable de n8n.
        Prioriza la ruta de instalación configurada.
        Luego, intenta la ruta común de npm en APPDATA (Windows).
        Finalmente, asume que "n8n" está en el PATH del sistema.
        """
        n8n_install_path = self.config.get_nested("servicios", "n8n", "ruta_instalacion", default=None)
        
        # 1. Intentar la ruta de instalación configurada
        if n8n_install_path and os.path.isdir(n8n_install_path):
            # Buscar n8n.cmd o n8n.exe dentro de la carpeta configurada
            # o en node_modules/.bin si es una instalación local
            possible_paths = [n8n_install_path]
            if os.path.exists(os.path.join(n8n_install_path, "node_modules", ".bin")):
                possible_paths.append(os.path.join(n8n_install_path, "node_modules", ".bin"))

            for path in possible_paths:
                n8n_cmd_path = os.path.join(path, "n8n.cmd")
                n8n_exe_path = os.path.join(path, "n8n.exe")
                if os.path.exists(n8n_cmd_path):
                    self.logger_dashboard.log("INFO", self.lang.get("log_n8n_found_config_path", n8n_cmd_path))
                    return f"\"{n8n_cmd_path}\""
                elif os.path.exists(n8n_exe_path):
                    self.logger_dashboard.log("INFO", self.lang.get("log_n8n_found_config_path", n8n_exe_path))
                    return f"\"{n8n_exe_path}\""

        # 2. Intentar la ruta común de instalación global de npm en Windows
        if sys.platform == "win32":
            appdata_path = os.getenv("APPDATA")
            if appdata_path:
                npm_n8n_path = os.path.join(appdata_path, "npm", "n8n.cmd")
                if os.path.exists(npm_n8n_path):
                    self.logger_dashboard.log("INFO", self.lang.get("log_n8n_found_appdata", npm_n8n_path))
                    return f"\"{npm_n8n_path}\""

        # 3. Fallback: confía en que n8n está en el PATH
        self.logger_dashboard.log("WARNING", self.lang.get("log_n8n_not_found_common_paths"))
        return "n8n"

    def _get_ngrok_command_path(self):
        """
        Obtiene la ruta completa al ejecutable de ngrok (o ngrok.cmd en Windows)
        basándose en la configuración o asumiendo que está en PATH.
        """
        ngrok_exec_dir = self.config.get_nested("servicios", "ngrok", "ruta_ejecutable", default=None)
        
        if ngrok_exec_dir and os.path.isdir(ngrok_exec_dir):
            full_ngrok_exe_path = os.path.join(ngrok_exec_dir, "ngrok.exe")
            if os.path.exists(full_ngrok_exe_path):
                self.logger_dashboard.log("INFO", self.lang.get("log_ngrok_found_config_path", full_ngrok_exe_path))
                return f"\"{full_ngrok_exe_path}\""
            else:
                self.logger_dashboard.log("WARNING", self.lang.get("log_ngrok_not_found_config_path_fallback", full_ngrok_exe_path))
        
        self.logger_dashboard.log("WARNING", self.lang.get("log_ngrok_not_found_config_path"))
        return "ngrok" # Fallback al nombre del ejecutable si la ruta no se encuentra o no existe

    def _get_mailhog_command_path(self):
        """
        Obtiene la ruta absoluta al ejecutable de MailHog.
        Prioriza la ruta configurada. Si no es válida, asume que está en PATH.
        """
        mailhog_exec_path_config = self.config.get_nested("servicios", "mailhog", "ruta_ejecutable", default=None)
        
        if mailhog_exec_path_config:
            # Caso 1: La ruta configurada es directamente el archivo ejecutable
            if os.path.isfile(mailhog_exec_path_config) and mailhog_exec_path_config.lower().endswith("mailhog_windows_amd64.exe"):
                self.logger_dashboard.log("INFO", self.lang.get("log_mailhog_found_config_path", mailhog_exec_path_config))
                return f"\"{mailhog_exec_path_config}\""
            # Caso 2: La ruta configurada es un directorio que contiene el ejecutable
            elif os.path.isdir(mailhog_exec_path_config):
                full_mailhog_exe_path = os.path.join(mailhog_exec_path_config, "MailHog_windows_amd64.exe")
                if os.path.exists(full_mailhog_exe_path):
                    self.logger_dashboard.log("INFO", self.lang.get("log_mailhog_found_config_path", full_mailhog_exe_path))
                    return f"\"{full_mailhog_exe_path}\""
                else:
                    self.logger_dashboard.log("WARNING", self.lang.get("log_mailhog_not_found_config_path_fallback", full_mailhog_exe_path))
            else:
                # La ruta configurada no es ni un archivo ni un directorio válido, se registra una advertencia
                self.logger_dashboard.log("WARNING", self.lang.get("log_mailhog_invalid_config_path", mailhog_exec_path_config))
        
        # Fallback: Si no se encontró en la ruta configurada o la ruta era inválida, asume que está en PATH
        self.logger_dashboard.log("WARNING", self.lang.get("log_mailhog_not_found_config_path"))
        return "MailHog_windows_amd64.exe" # Fallback: asume que está en system PATH


    def iniciar_n8n(self):
        """Lanza n8n directamente en una nueva consola."""
        self.logger_dashboard.log("INFO", self.lang.get("log_n8n_starting"))
        try:
            n8n_port = self.config.get_nested("servicios", "n8n", "puerto", default=self.N8N_WEB_PORT)
            n8n_cmd_path = self._get_n8n_command_path().strip('\"') # Ruta sin comillas

            if not n8n_cmd_path:
                self.logger_dashboard.log("ERROR", self.lang.get("n8n_not_found_error"))
                return False, self.lang.get("n8n_not_found_message")

            command_to_execute = []
            if n8n_cmd_path.lower().endswith(".cmd"):
                # Para archivos .cmd, necesitamos ejecutarlo a través de cmd.exe
                command_to_execute = ["cmd.exe", "/c", "start", "cmd.exe", "/k", n8n_cmd_path]
            else:
                # Para archivos .exe o comandos en PATH, podemos ejecutar directamente con 'start'
                command_to_execute = ["cmd.exe", "/c", "start", n8n_cmd_path]
            
            # Añadir los argumentos específicos de n8n
            command_to_execute.extend(["--port", str(n8n_port)])

            self.logger_dashboard.log("INFO", self.lang.get("log_n8n_command", ' '.join(command_to_execute)))

            self.n8n_process = subprocess.Popen(command_to_execute, creationflags=subprocess.CREATE_NEW_CONSOLE)
            time.sleep(10) # Dar tiempo a n8n para iniciar y abrir el puerto

            if self._puerto_activo(n8n_port):
                self.logger_dashboard.log("INFO", self.lang.get("n8n_status_active"))
                return True, self.lang.get("n8n_started_message")
            else:
                self.logger_dashboard.log("ERROR", self.lang.get("n8n_status_connection_error"))
                return False, self.lang.get("n8n_start_failed_message")
        except FileNotFoundError:
            self.logger_dashboard.log("ERROR", self.lang.get("n8n_not_found_error"))
            return False, self.lang.get("n8n_not_found_message")
        except Exception as e:
            self.logger_dashboard.log("CRITICAL", self.lang.get("log_n8n_start_failed", str(e)))
            return False, self.lang.get("n8n_start_failed_message")

    def detener_n8n(self):
        """Intenta detener n8n usando taskkill."""
        self.logger_dashboard.log("INFO", self.lang.get("log_n8n_stopping"))
        try:
            # Intentar terminar el proceso si lo iniciamos nosotros
            if self.n8n_process and self.n8n_process.poll() is None:
                self.n8n_process.terminate()
                self.n8n_process.wait(timeout=5)
                self.n8n_process = None
                self.logger_dashboard.log("INFO", self.lang.get("n8n_stopped_message"))
                return True, self.lang.get("n8n_stopped_message")
            
            # Fallback a taskkill si no lo iniciamos o si terminate no funciona
            subprocess.run(["taskkill", "/F", "/IM", "n8n.cmd"], capture_output=True, text=True, check=False)
            subprocess.run(["taskkill", "/F", "/IM", "n8n.exe"], capture_output=True, text=True, check=False) # Por si es .exe
            
            # Verificar si el puerto sigue activo
            n8n_port = self.config.get_nested("servicios", "n8n", "puerto", default=self.N8N_WEB_PORT)
            if not self._puerto_activo(n8n_port):
                self.logger_dashboard.log("INFO", self.lang.get("n8n_stopped_message"))
                return True, self.lang.get("n8n_stopped_message")
            else:
                self.logger_dashboard.log("ERROR", self.lang.get("n8n_stop_failed_message", "Puerto de n8n sigue activo."))
                return False, self.lang.get("n8n_stop_failed_message")

        except Exception as e:
            self.logger_dashboard.log("ERROR", self.lang.get("log_n8n_stop_failed", str(e)))
            return False, self.lang.get("n8n_stop_failed_message")

    def reiniciar_n8n(self):
        """Detiene y luego inicia n8n."""
        self.logger_dashboard.log("INFO", self.lang.get("log_n8n_restarting"))
        stop_success, stop_msg = self.detener_n8n()
        time.sleep(2) # Pequeña pausa entre detener e iniciar
        start_success, start_msg = self.iniciar_n8n()
        
        if stop_success and start_success:
            self.logger_dashboard.log("INFO", self.lang.get("n8n_restarted_message"))
            return True, self.lang.get("n8n_restarted_message")
        else:
            final_msg = f"{self.lang.get('n8n_restart_failed_message')} (Detener: {stop_msg}, Iniciar: {start_msg})"
            self.logger_dashboard.log("ERROR", final_msg)
            return False, final_msg

    def iniciar_ngrok(self):
        """Intenta iniciar ngrok y copiar la URL pública."""
        self.logger_dashboard.log("INFO", self.lang.get("log_ngrok_starting"))
        ngrok_cmd_path = self._get_ngrok_command_path().strip('\"') # Eliminar comillas para el comando
        try:
            authtoken = self._get_ngrok_authtoken()
            if authtoken and authtoken != "TU_NGROK_AUTHTOKEN_AQUI":
                # Ejecutar authtoken sin abrir una nueva consola visible
                # Usamos subprocess.run para esperar a que termine el comando de authtoken
                auth_command_list = [ngrok_cmd_path, "authtoken", authtoken]
                subprocess.run(auth_command_list, capture_output=True, text=True, check=False)
                self.logger_dashboard.log("INFO", self.lang.get("ngrok_authtoken_set_log"))
            elif not authtoken or authtoken == "TU_NGROK_AUTHTOKEN_AQUI":
                self.logger_dashboard.log("WARNING", self.lang.get("ngrok_authtoken_missing_warning"))
                return False, self.lang.get("ngrok_authtoken_missing_message")

            # Comando para iniciar ngrok sin abrir una nueva consola visible
            # Redirigimos stdout y stderr para que no aparezcan en la consola principal si la hay,
            # y para que Popen pueda controlar el proceso directamente.
            tunnel_command_list = [ngrok_cmd_path, "http", str(self.N8N_WEB_PORT)]
            self.ngrok_process = subprocess.Popen(tunnel_command_list, 
                                                  stdout=subprocess.PIPE, 
                                                  stderr=subprocess.PIPE,
                                                  creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0) # No abrir ventana en Windows
            
            url = None
            for i in range(self.NGROK_API_RETRIES):
                try:
                    response = requests.get(self.NGROK_API_URL, timeout=self.NGROK_API_TIMEOUT_INITIAL)
                    data = response.json()
                    if data and 'tunnels' in data and len(data['tunnels']) > 0:
                        url = data['tunnels'][0]['public_url']
                        break
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, IndexError) as e:
                    self.logger_dashboard.log("WARNING", self.lang.get("log_ngrok_api_retry_warning", i+1, self.NGROK_API_RETRIES, str(e), self.NGROK_API_RETRY_DELAY))
                    time.sleep(self.NGROK_API_RETRY_DELAY)
            
            if url:
                pyperclip.copy(url)
                self.logger_dashboard.log("INFO", self.lang.get("log_ngrok_active_copied", url))
                return True, url
            else:
                self.logger_dashboard.log("CRITICAL", self.lang.get("log_ngrok_no_tunnel"))
                return False, self.lang.get("ngrok_no_tunnel_message")

        except FileNotFoundError:
            self.logger_dashboard.log("ERROR", self.lang.get("ngrok_not_found_error"))
            return False, self.lang.get("ngrok_not_found_message")
        except Exception as e:
            self.logger_dashboard.log("CRITICAL", self.lang.get("log_ngrok_generic_error", str(e)))
            return False, self.lang.get("ngrok_start_failed_message")

    def detener_ngrok(self):
        """Intenta detener el proceso de ngrok."""
        self.logger_dashboard.log("INFO", self.lang.get("log_ngrok_stopping"))
        try:
            # Intentar terminar el proceso si lo iniciamos nosotros
            if self.ngrok_process and self.ngrok_process.poll() is None:
                self.ngrok_process.terminate()
                self.ngrok_process.wait(timeout=5)
                self.ngrok_process = None
                self.logger_dashboard.log("INFO", self.lang.get("ngrok_stopped_message"))
                return True, self.lang.get("ngrok_stopped_message")

            # Fallback a taskkill si no lo iniciamos o si terminate no funciona
            subprocess.run(["taskkill", "/F", "/IM", "ngrok.exe"], capture_output=True, text=True, check=False)
            
            # Verificar si el puerto de la API de ngrok sigue activo
            if not self._puerto_activo(4040): # Puerto de la API de ngrok
                self.logger_dashboard.log("INFO", self.lang.get("ngrok_stopped_message"))
                return True, self.lang.get("ngrok_stopped_message")
            else:
                self.logger_dashboard.log("ERROR", self.lang.get("ngrok_stop_failed_message", "Puerto de ngrok sigue activo."))
                return False, self.lang.get("ngrok_stop_failed_message")

        except Exception as e:
            self.logger_dashboard.log("ERROR", self.lang.get("log_ngrok_stop_failed", str(e)))
            return False, self.lang.get("ngrok_stop_failed_message")

    def iniciar_mailhog(self):
        """Lanza MailHog en consola nueva y verifica si está activo."""
        self.logger_dashboard.log("INFO", self.lang.get("log_mailhog_starting"))
        try:
            web_port = self.config.get_nested("servicios", "mailhog", "puerto_web", default=self.MAILHOG_WEB_PORT)
            smtp_port = self.config.get_nested("servicios", "mailhog", "puerto_smtp", default=self.MAILHOG_SMTP_PORT)
            mailhog_exec_path = self._get_mailhog_command_path().strip('\"') # Eliminar comillas para el comando

            # Verifica si MailHog ya está corriendo
            if self._puerto_activo(web_port):
                self.logger_dashboard.log("WARNING", self.lang.get("mailhog_already_running_message"))
                return True, self.lang.get("mailhog_already_running_message")

            # Intenta detener posibles instancias previas
            self.detener_mailhog()
            time.sleep(2) # Dar tiempo para que el proceso se cierre

            # Lanzar el proceso en nueva consola
            if not mailhog_exec_path:
                self.logger_dashboard.log("ERROR", self.lang.get("mailhog_not_found_error"))
                return False, self.lang.get("mailhog_not_found_message")

            command_list = [
                "cmd.exe", "/c", "start", "cmd.exe", "/k", mailhog_exec_path,
                f"-api-bind-addr=:{web_port}",
                f"-smtp-bind-addr=:{smtp_port}"
            ]
            
            self.logger_dashboard.log("INFO", self.lang.get("log_mailhog_command", ' '.join(command_list)))

            self.mailhog_process = subprocess.Popen(command_list, creationflags=subprocess.CREATE_NEW_CONSOLE)
            
            # Bucle de reintentos para verificar el puerto de MailHog
            mailhog_started = False
            for i in range(self.MAILHOG_API_RETRIES):
                if self._puerto_activo(web_port):
                    mailhog_started = True
                    break
                self.logger_dashboard.log("WARNING", self.lang.get("log_mailhog_api_retry_warning", i+1, self.MAILHOG_API_RETRIES, self.MAILHOG_RETRY_DELAY))
                time.sleep(self.MAILHOG_RETRY_DELAY)

            if mailhog_started:
                self.logger_dashboard.log("INFO", self.lang.get("mailhog_status_active"))
                return True, self.lang.get("mailhog_started_message")
            else:
                self.logger_dashboard.log("ERROR", self.lang.get("mailhog_status_connection_error"))
                return False, self.lang.get("mailhog_start_failed_message")

        except FileNotFoundError:
            self.logger_dashboard.log("ERROR", self.lang.get("mailhog_not_found_error"))
            return False, self.lang.get("mailhog_not_found_message")
        except Exception as e:
            self.logger_dashboard.log("CRITICAL", self.lang.get("log_mailhog_generic_error", str(e)))
            return False, self.lang.get("mailhog_start_failed_message")

    def detener_mailhog(self):
        """Intenta detener el proceso de MailHog."""
        self.logger_dashboard.log("INFO", self.lang.get("log_mailhog_stopping"))
        try:
            # Intentar terminar el proceso si lo iniciamos nosotros
            if self.mailhog_process and self.mailhog_process.poll() is None:
                self.mailhog_process.terminate()
                self.mailhog_process.wait(timeout=5)
                self.mailhog_process = None
                self.logger_dashboard.log("INFO", self.lang.get("mailhog_stopped_message"))
                return True, self.lang.get("mailhog_stopped_message")

            # Fallback a taskkill
            subprocess.run(["taskkill", "/F", "/IM", "MailHog_windows_amd64.exe"], capture_output=True, text=True, check=False)
            
            # Verificar si el puerto web de MailHog sigue activo
            mailhog_web_port = self.config.get_nested("servicios", "mailhog", "puerto_web", default=self.MAILHOG_WEB_PORT)
            if not self._puerto_activo(mailhog_web_port):
                self.logger_dashboard.log("INFO", self.lang.get("mailhog_stopped_message"))
                return True, self.lang.get("mailhog_stopped_message")
            else:
                self.logger_dashboard.log("ERROR", self.lang.get("mailhog_stop_failed_message", "Puerto de MailHog sigue activo."))
                return False, self.lang.get("mailhog_stop_failed_message")

        except Exception as e:
            self.logger_dashboard.log("ERROR", self.lang.get("mailhog_stop_failed_message", str(e)))
            return False, self.lang.get("mailhog_stop_failed_message")

    def check_n8n_status(self):
        """Verifica si n8n está activo haciendo una petición a su interfaz web."""
        n8n_port = self.config.get_nested("servicios", "n8n", "puerto", default=self.N8N_WEB_PORT)
        if self._puerto_activo(n8n_port):
            return "n8n_status_active",
        else:
            return "n8n_status_connection_error",

    def check_ngrok_status(self):
        """Verifica si ngrok tiene un túnel activo a través de su API."""
        try:
            response = requests.get(self.NGROK_API_URL, timeout=2)
            data = response.json()
            if data and 'tunnels' in data and len(data['tunnels']) > 0:
                url = data['tunnels'][0]['public_url']
                return "ngrok_status_active", url
            else:
                return "ngrok_status_no_tunnel",
        except requests.exceptions.ConnectionError:
            return "ngrok_status_connection_error_api",
        except requests.exceptions.Timeout:
            return "ngrok_api_timeout",
        except Exception as e:
            return "ngrok_status_generic_error", str(e)

    def check_mailhog_status(self):
        """Verifica si MailHog está activo."""
        mailhog_web_port = self.config.get_nested("servicios", "mailhog", "puerto_web", default=self.MAILHOG_WEB_PORT)
        if self._puerto_activo(mailhog_web_port):
            return "mailhog_status_active",
        else:
            return "mailhog_status_connection_error",