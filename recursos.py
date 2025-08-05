import os
import sys
import logging

class Recursos:
    """
    Clase para gestionar las rutas de los recursos de la aplicación,
    adaptándose a entornos empaquetados con PyInstaller.
    """
    @staticmethod
    def ruta_base_app():
        """
        Determina la ruta base de la aplicación.
        En modo PyInstaller, es sys._MEIPASS.
        En modo desarrollo, es el directorio del script principal.
        """
        if getattr(sys, 'frozen', False):
            # Estamos dentro de un ejecutable (.exe) creado por PyInstaller
            return sys._MEIPASS
        else:
            # Modo desarrollo (.py normal)
            # os.path.dirname(__file__) obtiene el directorio del archivo actual (recursos.py)
            return os.path.abspath(os.path.dirname(__file__))

    @staticmethod
    def ruta(archivo, carpeta=None):
        """
        Construye la ruta completa a un archivo dentro de una carpeta de recursos relativa a la base.
        Muestra una advertencia en el logger si el archivo no existe.
        """
        base_path = Recursos.ruta_base_app()
        if carpeta:
            ruta_completa = os.path.join(base_path, carpeta, archivo)
        else:
            ruta_completa = os.path.join(base_path, archivo)

        # Se registra una advertencia en el logger 'Dashboard' si el archivo no se encuentra
        if not os.path.exists(ruta_completa):
            logging.getLogger("Dashboard").warning(f"⚠️ Advertencia (Recursos): No se encontró el archivo '{archivo}' en la ruta: {ruta_completa}")
        return ruta_completa

    @staticmethod
    def icono():
        """
        Devuelve la ruta al archivo del icono de la aplicación.
        Se espera que 'n8n_icon.ico' esté dentro de la carpeta 'recursos'
        tanto en el proyecto como en el ejecutable, según tu .spec.
        """
        return Recursos.ruta("n8n_icon.ico", carpeta="recursos")

    @staticmethod
    def logo():
        """
        Devuelve la ruta al archivo del logo principal.
        Se espera que 'n8n_control_logo.png' esté dentro de la carpeta 'recursos'.
        """
        return Recursos.ruta("n8n_control_logo.png", carpeta="recursos")

    @staticmethod
    def config_usuario():
        """
        Devuelve la ruta al archivo de configuración de usuario.
        Se espera que 'usuario_config.json' esté dentro de la carpeta 'config'.
        """
        return Recursos.ruta("usuario_config.json", carpeta="config")

    @staticmethod
    def idioma(nombre_idioma):
        """
        Devuelve la ruta al archivo JSON de un idioma específico.
        Se espera que los archivos de idioma estén dentro de la carpeta 'idiomas'.
        """
        return Recursos.ruta(f"{nombre_idioma}.json", carpeta="idiomas")
