import subprocess
import time
import requests
import pyperclip
import os
import json
import sys
import socket
import logging

class Servicios:
    N8N_WEB_PORT = 5678
    NGROK_API_URL = "http://localhost:4040/api/tunnels"
    MAILHOG_WEB_PORT = 8025
    MAILHOG_SMTP_PORT = 1025

    def __init__(self, logger_dashboard, lang_manager, config):
        self.logger_dashboard = logger_dashboard
        self.lang = lang_manager
        self.config = config
        self.n8n_process = None
        self.ngrok_process = None
        self.mailhog_process = None

    def _puerto_activo(self, puerto):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.settimeout(0.1)
                return s.connect_ex(('localhost', puerto)) == 0
            except Exception:
                return False

    def _get_n8n_command_path(self):
        ruta_config = self.config.get_nested("servicios", "n8n", "ruta_instalacion", default=None)
        print("[DEBUG] ruta_instalacion desde JSON:", ruta_config)

        if ruta_config:
            if ruta_config.lower().endswith(".cmd") and os.path.isfile(ruta_config):
                return f"\"{ruta_config}\""
            elif os.path.isdir(ruta_config):
                for subpath in ["", "node_modules/.bin"]:
                    candidate = os.path.join(ruta_config, subpath, "n8n.cmd")
                    if os.path.isfile(candidate):
                        return f"\"{candidate}\""
        return "n8n"

    def _get_ngrok_command_path(self):
        ruta = self.config.get_nested("servicios", "ngrok", "ruta_ejecutable", default=None)
        print("[DEBUG] ruta_ejecutable ngrok desde JSON:", ruta)

        if ruta:
            if ruta.lower().endswith(".exe") and os.path.isfile(ruta):
                return f"\"{ruta}\""
            elif os.path.isdir(ruta):
                exe_path = os.path.join(ruta, "ngrok.exe")
                if os.path.isfile(exe_path):
                    return f"\"{exe_path}\""
        return "ngrok"

    def _get_mailhog_command_path(self):
        ruta = self.config.get_nested("servicios", "mailhog", "ruta_ejecutable", default=None)
        print("[DEBUG] ruta_ejecutable MailHog desde JSON:", ruta)

        if ruta:
            if ruta.lower().endswith(".exe") and os.path.isfile(ruta):
                return f"\"{ruta}\""
            elif os.path.isdir(ruta):
                exe_path = os.path.join(ruta, "MailHog_windows_amd64.exe")
                if os.path.isfile(exe_path):
                    return f"\"{exe_path}\""
        return "MailHog_windows_amd64.exe"

    def iniciar_n8n(self):
        self.logger_dashboard.log("INFO", self.lang.get("log_n8n_starting"))
        path = self._get_n8n_command_path().strip("\"")
        port = self.config.get_nested("servicios", "n8n", "puerto", default=self.N8N_WEB_PORT)
        if not os.path.isfile(path):
            self.logger_dashboard.log("ERROR", "n8n no encontrado en la ruta.")
            print("[ERROR] Ruta n8n inválida:", path)
            return False, "Ruta inválida para n8n"

        cmd = ["cmd.exe", "/c", "start", "cmd.exe", "/k", path, "--port", str(port)]
        print("[DEBUG] Comando n8n:", ' '.join(cmd))
        self.n8n_process = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
        time.sleep(10)
        activo = self._puerto_activo(port)
        return (True, "n8n iniciado") if activo else (False, "n8n no se conectó")

    def iniciar_ngrok(self):
        self.logger_dashboard.log("INFO", self.lang.get("log_ngrok_starting"))
        path = self._get_ngrok_command_path().strip("\"")
        port = self.N8N_WEB_PORT
        if not os.path.isfile(path):
            self.logger_dashboard.log("ERROR", "ngrok.exe no se encontró.")
            print("[ERROR] Ruta ngrok inválida:", path)
            return False, "Ruta inválida para ngrok"

        cmd = [path, "http", str(port)]
        print("[DEBUG] Comando ngrok:", ' '.join(cmd))
        self.ngrok_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                              creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
        for i in range(10):
            try:
                res = requests.get(self.NGROK_API_URL, timeout=5).json()
                url = res['tunnels'][0]['public_url']
                pyperclip.copy(url)
                return True, url
            except:
                time.sleep(1)
        return False, "ngrok no levantó túnel"

    def iniciar_mailhog(self):
        self.logger_dashboard.log("INFO", self.lang.get("log_mailhog_starting"))
        path = self._get_mailhog_command_path().strip("\"")
        web_port = self.config.get_nested("servicios", "mailhog", "puerto_web", default=self.MAILHOG_WEB_PORT)
        smtp_port = self.config.get_nested("servicios", "mailhog", "puerto_smtp", default=self.MAILHOG_SMTP_PORT)

        if not os.path.isfile(path):
            self.logger_dashboard.log("ERROR", "MailHog.exe no encontrado.")
            print("[ERROR] Ruta MailHog inválida:", path)
            return False, "Ruta inválida para MailHog"

        cmd = ["cmd.exe", "/c", "start", "cmd.exe", "/k", path,
               f"-api-bind-addr=:{web_port}", f"-smtp-bind-addr=:{smtp_port}"]
        print("[DEBUG] Comando MailHog:", ' '.join(cmd))
        self.mailhog_process = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)

        for i in range(10):
            if self._puerto_activo(web_port):
                return True, "MailHog activo"
            time.sleep(1)
        return False, "MailHog no respondió"

    def check_n8n_status(self):
        puerto = self.config.get_nested("servicios", "n8n", "puerto", default=self.N8N_WEB_PORT)
        if self._puerto_activo(puerto):
            return "n8n_activo", f"http://localhost:{puerto}"
        return "n8n_inactivo", f"Puerto {puerto} no responde"

    def check_mailhog_status(self):
        puerto_web = self.config.get_nested("servicios", "mailhog", "puerto_web", default=self.MAILHOG_WEB_PORT)
        if self._puerto_activo(puerto_web):
            return "mailhog_activo", f"http://localhost:{puerto_web}"
        return "mailhog_inactivo", f"Puerto {puerto_web} no responde"

    def check_ngrok_status(self):
        try:
            response = requests.get(self.NGROK_API_URL, timeout=3).json()
            tunnel_url = response['tunnels'][0]['public_url']
            return "ngrok_activo", tunnel_url
        except Exception:
            return "ngrok_inactivo", "No hay túnel activo en ngrok"