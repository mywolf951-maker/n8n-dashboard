# launcher.py

import servicios.n8n as n8n
import servicios.ngrok as ngrok
import servicios.mailhog as mailhog

class Launcher:
    def __init__(self):
        pass

    def separador(self):
        print("\n" + "-" * 50 + "\n")

    def resumen_servicios(self):
        print("🧠 Lanzando servicios del dashboard modular...\n")
        self.separador()

        print("🔧 n8n")
        n8n.lanzar_n8n()
        self.separador()

        print("🌐 ngrok")
        ngrok.lanzar_ngrok()
        self.separador()

        print("📮 MailHog")
        mailhog.lanzar_mailhog()
        self.separador()

        print("✅ Todos los servicios han sido lanzados. Verifica los logs y puertos para confirmar estado.")
        print("📊 Puedes integrar este launcher en tu GUI para control total desde botones.")
