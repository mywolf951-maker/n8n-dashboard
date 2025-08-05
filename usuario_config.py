import json
import os
import logging
from recursos import Recursos # Asumiendo que Recursos está disponible para la gestión de rutas

class ConfigUsuario:
    """
    Gestiona la carga y guardado de las preferencias de usuario
    desde un archivo JSON.
    """
    def __init__(self):
        self.prefs_path = Recursos.config_usuario()
        self.logger = logging.getLogger("Dashboard") # Usar el mismo logger global
        self.preferences = self._load_preferences()

    def _load_preferences(self):
        """Carga las preferencias desde el archivo JSON."""
        if os.path.exists(self.prefs_path):
            try:
                with open(self.prefs_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                self.logger.error(f"Error al leer preferencias JSON desde {self.prefs_path}: {e}")
                return {} # Devolver un diccionario vacío en caso de error de formato
            except Exception as e:
                self.logger.error(f"Error inesperado al cargar preferencias desde {self.prefs_path}: {e}")
                return {}
        return {} # Devolver un diccionario vacío si el archivo no existe

    def _save_preferences(self):
        """Guarda las preferencias en el archivo JSON."""
        os.makedirs(os.path.dirname(self.prefs_path), exist_ok=True)
        try:
            with open(self.prefs_path, "w", encoding="utf-8") as f:
                json.dump(self.preferences, f, indent=4) # indent=4 para formato legible
        except Exception as e:
            self.logger.error(f"Error al guardar preferencias en {self.prefs_path}: {e}")

    def get(self, key, default=None):
        """Obtiene una preferencia por clave, con un valor por defecto si no existe."""
        return self.preferences.get(key, default)

    def set(self, key, value):
        """Establece una preferencia por clave y guarda los cambios en el archivo."""
        self.preferences[key] = value
        self._save_preferences()

    def get_nested(self, *keys, default=None):
        """
        Obtiene un valor anidado dentro de las preferencias utilizando una secuencia de claves.
        Ejemplo: config.get_nested("servicios", "n8n", "puerto", default=5678)
        """
        data = self.preferences
        for key in keys:
            if isinstance(data, dict):
                data = data.get(key, {})
            else:
                # Si en algún punto 'data' no es un diccionario, no se puede seguir anidando
                return default
        return data if data else default

