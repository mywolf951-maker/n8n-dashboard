from app import App
from usuario_config import ConfigUsuario
from language_manager import LanguageManager
import tkinter.messagebox as messagebox

try:
    config = ConfigUsuario()
    idioma = config.get("idioma", "es")
    lang = LanguageManager(idioma)

    app = App(lang, config)
    app.mainloop()

except Exception as e:
    print(f"Error al iniciar la app: {e}")
    lang = LanguageManager("es")
    messagebox.showerror(
        lang.get("Error"),
        lang.get("Error inesperado al iniciar la aplicación")
    )
