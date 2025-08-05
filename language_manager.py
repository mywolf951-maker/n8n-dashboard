import json
import logging
from recursos import Recursos # Importar Recursos para manejar la ruta del idioma

class LanguageManager:
    """
    Gestiona la carga y recuperación de textos en diferentes idiomas
    desde archivos JSON.
    """
    def __init__(self, idioma="es"):
        self.idioma = idioma
        try:
            # La ruta del archivo de idioma ahora usa Recursos.ruta
            ruta = Recursos.ruta(f"{idioma}.json", carpeta="idiomas")
            with open(ruta, "r", encoding="utf-8") as f:
                self.textos = json.load(f)
        except FileNotFoundError:
            logging.getLogger("Dashboard").error(f"Archivo de idioma '{idioma}.json' no encontrado en {Recursos.ruta('', 'idiomas')}. Usando claves por defecto.")
            self.textos = {} # Usar un diccionario vacío si el archivo no se encuentra
        except json.JSONDecodeError as e:
            logging.getLogger("Dashboard").error(f"Error al parsear archivo de idioma '{idioma}.json': {e}. Usando claves por defecto.")
            self.textos = {}

    def get(self, clave, *args):
        """
        Obtiene el texto para una clave dada.
        Si se proporcionan argumentos, los formatea en el texto.
        Devuelve la clave si el texto no existe.
        """
        texto = self.textos.get(clave, clave)
        if args:
            try:
                return texto.format(*args)
            except IndexError:
                logging.getLogger("Dashboard").warning(f"Error de formato para la clave '{clave}' con argumentos {args}. Texto original: '{texto}'")
                return texto
        return texto

