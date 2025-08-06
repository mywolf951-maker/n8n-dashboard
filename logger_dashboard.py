import logging


class LoggerDashboard:
    def __init__(self, app_instance=None, lang_manager=None):
        self.app = app_instance
        self.lang = lang_manager
        self.log_textbox = None

    def set_log_textbox(self, textbox_widget):
        """Conecta el panel de logs para actualizarlo en tiempo real."""
        self.log_textbox = textbox_widget

    def log(self, nivel, clave, extra_info=None):
        """
        Registra eventos y los muestra si el panel de logs está conectado.

        :param nivel: Nivel de log ('INFO', 'WARNING', 'ERROR', etc.)
        :param clave: Clave del mensaje a traducir o mensaje directo
        :param extra_info: Datos adicionales opcionales
        """
        mensaje = self.lang.get(clave, extra_info) if self.lang else f"{clave}: {extra_info}"

        # Registro en consola
        print(f"[{nivel}] {mensaje}")

        # Registro en el textbox si está presente
        if self.log_textbox:
            self.log_textbox.insert("end", f"[{nivel}] {mensaje}\n")
            self.log_textbox.see("end")

        # Registro en archivo si se ha configurado
        logger = logging.getLogger("n8n-dashboard")
        if logger.hasHandlers():
            logger_method = getattr(logger, nivel.lower(), logger.info)
            logger_method(mensaje)


def crear_logger():
    """
    Crea un logger de archivo para registrar en 'actividad_log.txt'
    Evita duplicación de handlers en múltiples llamadas.
    """
    logger = logging.getLogger("n8n-dashboard")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.FileHandler("actividad_log.txt", encoding="utf-8")
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
