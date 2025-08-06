import os
import sys
import datetime
from PIL import ImageGrab
import requests
import smtplib
from email.message import EmailMessage
import pyperclip
import time

# 🎯 Acceso a recursos empaquetados
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# 📸 Captura visual del widget ante error
def capturar_widget(widget, nombre="captura_error"):
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
        return True, archivo
    except Exception as e:
        return False, str(e)

# 📧 Envío por MailHog con captura adjunta
def enviar_a_mailhog(ruta_imagen, subject, content, from_email="dashboard@localhost", to_email="monitor@localhost"):
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

        return True, "capture_sent"
    except Exception as e:
        return False, str(e)

# 🧪 Verificación de MailHog
def verificar_mailhog():
    try:
        response = requests.get("http://localhost:8025", timeout=2)
        if response.status_code == 200:
            return True, "mailhog_status_active"
        else:
            return False, "mailhog_status_inaccessible_code", response.status_code
    except requests.exceptions.ConnectionError:
        return False, "mailhog_status_connection_error"
    except requests.exceptions.Timeout:
        return False, "mailhog_status_timeout"
    except Exception as e:
        return False, "mailhog_status_generic_error", str(e)

# 🌐 Extracción inteligente del túnel ngrok
def obtener_url_ngrok():
    for intento in range(5):
        try:
            time.sleep(1.5)
            response = requests.get("http://localhost:4040/api/tunnels")
            data = response.json()
            url = data['tunnels'][0]['public_url']
            pyperclip.copy(url)
            print(f"🌐 ngrok activo en: {url} (copiado al portapapeles)")
            return url
        except Exception as e:
            print(f"Intento {intento+1}: ngrok aún no responde...")
    print("❌ No se pudo obtener la URL pública de ngrok.")
    return None