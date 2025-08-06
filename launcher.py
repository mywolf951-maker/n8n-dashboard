import servicios.n8n as n8n
import servicios.ngrok as ngrok
import servicios.mailhog as mailhog
import time


def separador():
    print("\n" + "-" * 50 + "\n")


def resumen_servicios():
    print("🧠 Lanzando servicios del dashboard modular...\n")
    separador()

    print("🔧 n8n")
    n8n.lanzar_n8n()
    separador()

    print("🌐 ngrok")
    ngrok.lanzar_ngrok()
    separador()

    print("📮 MailHog")
    mailhog.lanzar_mailhog()
    separador()

    print("✅ Todos los servicios han sido lanzados. Verifica los logs y puertos para confirmar estado.")
    print("📊 Puedes integrar este launcher en tu GUI para control total desde botones.")


if __name__ == "__main__":
    resumen_servicios()
