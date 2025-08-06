class Servicios:
    def __init__(self, logger, lang, config):
        self.logger = logger
        self.lang = lang
        self.config = config

        # Rutas desde el config JSON
        self.n8n_path = config.get("servicios", {}).get("n8n", {}).get("ruta_instalacion", "")
        self.ngrok_path = config.get("servicios", {}).get("ngrok", {}).get("ruta_ejecutable", "")
        self.mailhog_path = config.get("servicios", {}).get("mailhog", {}).get("mailhog_exec_path", "")

        # Puertos
        self.n8n_port = config.get("servicios", {}).get("n8n", {}).get("puerto", 5678)
        self.mailhog_smtp_port = config.get("servicios", {}).get("mailhog", {}).get("puerto_smtp", 1025)
        self.mailhog_web_port = config.get("servicios", {}).get("mailhog", {}).get("puerto_web", 8025)

        # Autenticación y región para ngrok
        self.ngrok_token = config.get("servicios", {}).get("ngrok", {}).get("authtoken", "")
        self.ngrok_region = config.get("servicios", {}).get("ngrok", {}).get("region", "us")

        self.logger.log("Servicios cargados correctamente.")
        # Aquí puedes añadir llamadas a métodos para validar rutas o iniciar servicios

    # Ejemplo de método para verificar rutas
    def verificar_rutas(self):
        import os
        resultados = {
            "n8n": os.path.exists(self.n8n_path),
            "ngrok": os.path.exists(self.ngrok_path),
            "mailhog": os.path.exists(self.mailhog_path)
        }
        return resultados