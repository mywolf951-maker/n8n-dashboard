import os
import subprocess
import time
import requests
import json

def cargar_ruta_ngrok():
    with open("config/rutas.json", "r") as archivo:
        rutas = json.load(archivo)
    return rutas.get("ngrok")

def lanzar_ngrok():
    ruta = cargar_ruta_ngrok()
    if not ruta or not os.path.exists(ruta):
        print("❌ Ruta de ngrok no válida.")
        return

    # Lanzar ngrok en background
    comando = [
        "cmd.exe", "/c", "start", "cmd.exe", "/k",
        f"{ruta} http 5678"
    ]
    subprocess.Popen(comando)
    print("🚀 ngrok lanzado. Esperando túnel...")

    # Verificar si el túnel está activo
    for intento in range(10):
        try:
            response = requests.get("http://localhost:4040/api/tunnels")
            if response.status_code == 200 and "tunnels" in response.json():
                print("✅ ngrok está corriendo y el túnel está activo.")
                return
        except:
            pass
        print(f"⏳ Intento {intento + 1}/10: esperando túnel...")
        time.sleep(1)

    print("❌ Error: ngrok no respondió en localhost:4040.")

if __name__ == "__main__":
    lanzar_ngrok()