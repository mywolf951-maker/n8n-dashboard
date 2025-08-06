import os
import subprocess
import time
import requests
import json

def cargar_ruta_mailhog():
    with open("config/rutas.json", "r") as archivo:
        rutas = json.load(archivo)
    return rutas.get("mailhog")

def lanzar_mailhog():
    ruta = cargar_ruta_mailhog()
    if not ruta or not os.path.exists(ruta):
        print("❌ Ruta de MailHog no válida.")
        return

    os.chdir(os.path.dirname(ruta))
    comando = [
        "cmd.exe", "/c", "start", "cmd.exe", "/k",
        f"{ruta} -api-bind-addr=:8025 -smtp-bind-addr=:1025"
    ]
    subprocess.Popen(comando)
    print("🚀 MailHog lanzado. Esperando respuesta...")

    # Verificación con reintentos
    for intento in range(10):
        try:
            response = requests.get("http://localhost:8025")
            if response.status_code == 200:
                print("✅ MailHog está corriendo correctamente.")
                return
        except:
            pass
        print(f"⏳ Intento {intento + 1}/10: esperando puerto...")
        time.sleep(1)

    print("❌ Error: MailHog no respondió en el puerto 8025.")

if __name__ == "__main__":
    lanzar_mailhog()