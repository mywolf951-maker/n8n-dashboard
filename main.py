import sys
from tkinter import messagebox
from app import App
from usuario_config import ConfigUsuario
from language_manager import LanguageManager

def lanzar_app():
    """
    Función principal para lanzar la aplicación GUI.
    Incluye manejo de errores para la inicialización de la app,
    mostrando mensajes localizados en caso de fallo.
    """
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        # Cargar configuración de usuario para obtener la preferencia de idioma
        config = ConfigUsuario()
        idioma = config.get("idioma", "es") # Lee del JSON: "idioma": "es", por defecto "es"
        
        # Inicializar el gestor de idiomas con el idioma preferido
        lang = LanguageManager(idioma)

        # Obtener los textos traducidos para el título y mensaje del error
        titulo = lang.get("error_app_title")
        mensaje = lang.get("error_app_message", str(e)) # Pasa el error como argumento para formatear

        # Mostrar ventana emergente informativa con el mensaje traducido
        messagebox.showerror(title=titulo, message=mensaje)
        sys.exit(1) # Salir con un código de error

if __name__ == "__main__":
    lanzar_app()

