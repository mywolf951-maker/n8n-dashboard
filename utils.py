import os
import datetime
from PIL import ImageGrab
import requests
import smtplib
from email.message import EmailMessage
# No importar logging directamente aquí, se espera que el logger se pase o se use el global.
# Las funciones devuelven mensajes "crudos" o claves para que el llamador los traduzca.

def capturar_widget(widget, nombre="captura_error"):
    """
    Captura una imagen de un widget específico de la interfaz gráfica.
    Devuelve True y la ruta del archivo si tiene éxito, False y un mensaje de error si falla.
    """
    try:
        x = widget.winfo_rootx()
        y = widget.winfo_rooty()
        w = widget.winfo_width()
        h = widget.winfo_height()

        bbox = (x, y, x + w, y + h)

        carpeta = "capturas"
        os.makedirs(carpeta, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo = f"{carpeta}/{nombre}_{timestamp}.png"

        imagen = ImageGrab.grab(bbox)
        imagen.save(archivo)
        return True, archivo # Devuelve la ruta del archivo para que el llamador la use/traduzca

    except Exception as e:
        return False, str(e) # Devuelve el mensaje de error en crudo

def enviar_a_mailhog(ruta_imagen, subject, content, from_email="dashboard@localhost", to_email="monitor@localhost"):
    """
    Envía un correo electrónico con una imagen adjunta a un servidor MailHog.
    Devuelve True y una clave de éxito si tiene éxito, False y un mensaje de error si falla.
    """
    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        msg.set_content(content)

        with open(ruta_imagen, 'rb') as f:
            msg.add_attachment(f.read(), maintype='image', subtype='png', filename=os.path.basename(ruta_imagen))

        with smtplib.SMTP("localhost", 1025) as server:
            server.send_message(msg)

        return True, "capture_sent" # Clave para traducción de éxito

    except Exception as e:
        return False, str(e) # Mensaje de error en crudo

def verificar_mailhog():
    """
    Verifica si el servidor MailHog está activo y accesible.
    Devuelve True y una clave de éxito si está activo, False y una clave/argumento de error si no.
    """
    try:
        response = requests.get("http://localhost:8025", timeout=2) # Añadir timeout para evitar esperas largas
        if response.status_code == 200:
            return True, "mailhog_status_active" # Clave para traducción
        else:
            return False, "mailhog_status_inaccessible_code", response.status_code # Clave y argumento para traducción
    except requests.exceptions.ConnectionError:
        return False, "mailhog_status_connection_error" # Clave para traducción
    except requests.exceptions.Timeout:
        return False, "mailhog_status_timeout" # Clave para traducción
    except Exception as e:
        return False, "mailhog_status_generic_error", str(e) # Clave y argumento para traducción


