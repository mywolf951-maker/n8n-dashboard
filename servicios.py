import subprocess
import os
import psutil
import logging
import time
import requests

logging.basicConfig(filename='actividad_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

class Servicios:
    # Rutas absolutas a los ejecutables
    RUTA_N8N = r'C:\Users\Aryn\AppData\Roaming\npm\n8n.cmd'
    RUTA_MAILHOG = r'C:\Users\Aryn\Desktop\n8n-control\Controlpro\MailHog_windows_amd64.exe'
    RUTA_NGROK = r'C:\Users\Aryn\Desktop\n8n-control\Controlpro\node_modules\@ngrok\ngrok-win32-x64-msvc\ngrok.exe'

    @staticmethod
    def esta_corriendo(nombre_proceso):
        try:
            return any(nombre_proceso.lower() in proc.name().lower() for proc in psutil.process_iter())
        except Exception as e:
            logging.error(f'Error al verificar {nombre_proceso}: {e}')
            return False

    @staticmethod
    def esperar_url(url, intentos=10, intervalo=1):
        for i in range(intentos):
            try:
                r = requests.get(url, timeout=1)
                if r.ok:
                    return True
            except:
                time.sleep(intervalo)
        return False

    @staticmethod
    def lanzar_servicio(nombre, ruta, argumentos=''):
        try:
            if Servicios.esta_corriendo(nombre):
                logging.info(f'{nombre} ya está corriendo')
                return f'{nombre} ya estaba activo'

            if not os.path.exists(ruta):
                logging.error(f'{nombre} no encontrado: {ruta}')
                return f'{nombre} error — archivo no encontrado'

            comando = f'"{ruta}" {argumentos}' if argumentos else f'"{ruta}"'
            subprocess.Popen(comando, shell=True)
            logging.info(f'{nombre} lanzado correctamente')
            return f'{nombre} lanzado'
        except Exception as e:
            logging.error(f'Error al lanzar {nombre}: {e}')
            return f'{nombre} error: {str(e)}'

    @staticmethod
    def lanzar_todos():
        logging.info("Inicio del arranque global")
        resultados = {}

        resultados['n8n'] = Servicios.lanzar_servicio('n8n', Servicios.RUTA_N8N)
        time.sleep(2)

        if Servicios.esperar_url("http://localhost:5678"):
            resultados['ngrok'] = Servicios.lanzar_servicio('ngrok', Servicios.RUTA_NGROK, 'http 5678')
        else:
            resultados['ngrok'] = "ngrok no se lanzó — n8n no respondió"

        resultados['MailHog'] = Servicios.lanzar_servicio('MailHog', Servicios.RUTA_MAILHOG)

        logging.info("Arranque global finalizado")
        return resultados

# Solo se ejecuta si abres este archivo directamente
if __name__ == "__main__":
    estados = Servicios.lanzar_todos()
    for servicio, estado in estados.items():
        print(f"{servicio}: {estado}")