import os
import json

# Cargar el archivo de configuración
with open("usuario_config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

print("\n🔍 Verificando rutas de ejecutables...\n")

# Función para verificar cada ruta
def verificar_ruta(nombre, ruta):
    if ruta and os.path.exists(ruta):
        print(f"✔ {nombre}: Ruta válida 👉 {ruta}")
    else:
        print(f"❌ {nombre}: Ruta NO encontrada ⚠️ {ruta}")

# Rutas a verificar
verificar_ruta("n8n.cmd", config["servicios"]["n8n"].get("ruta_instalacion"))
verificar_ruta("ngrok.exe", config["servicios"]["ngrok"].get("ruta_ejecutable"))
verificar_ruta("MailHog.exe", config["servicios"]["mailhog"].get("mailhog_exec_path"))

print("\n✅ Verificación completada.\n")