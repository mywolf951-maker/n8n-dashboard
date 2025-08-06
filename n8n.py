import os
import subprocess
import time
import requests
import json

def cargar_ruta_n8n():
    with open("config/rutas.json", "r") as archivo:
        rutas = json.load(archivo)
    return rutas.get("n8n")

def lanzar_n8n():
    ruta = cargar_ruta_n8n()
    if not ruta or not os.path.exists(ruta):
        print("❌ Ruta de n8n no válida.")
        return

    comando = [
        "cmd.exe", "/c", "start", "cmd.exe", "/k",
        f"{ruta} --port 5678"
    ]
    subprocess.Popen(comando)
    print("🚀 n8n lanzado. Esperando respuesta...")

    # Verificación con reintentos
    for intento in range(10):
        try:
            response = requests.get("http://localhost:5678")
            if response.status_code == 200:
                print("✅ n8n está corriendo correctamente.")
                return
        except:
            pass
        print(f"⏳ Intento {intento + 1}/10: esperando puerto...")
        time.sleep(1)

    print("❌ Error: n8n no respondió en el puerto 5678.")

if __name__ == "__main__":
    lanzar_n8n()