"""
BOT DIDI - VERSIÓN CON INTERFAZ GRÁFICA
Interfaz super simple para que cualquier usuario pueda usar el bot

ARQUITECTURA MODULAR:
- config/: Configuraciones globales
- backend/: Servidor Flask para registro en BD
- chrome/: Gestión y verificación de Chrome
- bot/: Lógica de procesamiento y navegación
- gui/: Interfaz gráfica Tkinter
"""
import tkinter as tk
from tkinter import messagebox
import time
import psutil
import requests
from threading import Thread
from gui.activation import mostrar_activacion
from gui.login import mostrar_login
from gui.interface import BotDidiGUI
from bot.main import ejecutar_bot
from backend.flask_server import iniciar_backend
from backend.license_utils import leer_token_local, generar_hardware_id


# Variables globales
token_global = None
usuario_global = None
clave_licencia_global = None


def iniciar_backend_startup():
    """Inicia el backend al arrancar la aplicación"""
    print("[*] Verificando puerto 5000...")

    # Limpiar puerto 5000 de ejecuciones anteriores
    procesos_cerrados = 0
    for proc in psutil.process_iter(['pid', 'name', 'connections']):
        try:
            for conn in proc.connections():
                if hasattr(conn, 'laddr') and conn.laddr.port == 5000:
                    print(f"[*] Cerrando proceso anterior en puerto 5000 (PID {proc.pid})...")
                    proc.kill()
                    procesos_cerrados += 1
                    time.sleep(1)
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, AttributeError):
            pass

    if procesos_cerrados > 0:
        print(f"[OK] {procesos_cerrados} proceso(s) cerrado(s)")
        time.sleep(2)
    else:
        print("[OK] Puerto 5000 libre")

    # Iniciar backend en thread
    print("[*] Iniciando backend Flask...")
    backend_thread = Thread(target=iniciar_backend, daemon=True)
    backend_thread.start()
    time.sleep(3)

    # Verificar que el backend esté disponible
    print("[*] Verificando backend...")
    for intento in range(5):
        try:
            response = requests.get('http://localhost:5000/health', timeout=3)
            if response.status_code == 200:
                print("[OK] Backend iniciado correctamente")
                return True
        except:
            if intento < 4:
                print(f"[*] Esperando backend... ({intento + 1}/5)")
                time.sleep(2)

    return False


def validar_licencia_con_servidor(clave, hardware_id):
    """Valida la licencia con el servidor"""
    try:
        response = requests.post(
            'http://localhost:5000/licencias/validar',
            json={
                'clave': clave,
                'hardware_id': hardware_id
            },
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] No se pudo validar licencia: {e}")
        return False


def on_activation_exitosa(clave):
    """Callback cuando la activación es exitosa"""
    global clave_licencia_global
    clave_licencia_global = clave
    print(f"[OK] Licencia activada: {clave}")
    # Continuar con el login
    mostrar_login(on_login_exitoso)


def on_login_exitoso(token, usuario):
    """Callback cuando el login es exitoso"""
    global token_global, usuario_global
    token_global = token
    usuario_global = usuario

    # Crear ventana principal del bot
    root = tk.Tk()
    app = BotDidiGUI(root, ejecutar_bot, token, usuario)
    root.mainloop()


def main():
    """Punto de entrada principal del programa"""
    print("=" * 60)
    print(" " * 15 + "BOT DIDI - INICIANDO")
    print("=" * 60)

    # PASO 1: Iniciar backend
    print("\n[1/3] Iniciando backend...")
    backend_ok = iniciar_backend_startup()

    if not backend_ok:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Error de Backend",
            "No se pudo iniciar el servidor backend.\n\n"
            "Posibles soluciones:\n"
            "1. Verifica que el puerto 5000 esté libre\n"
            "2. Reinicia la aplicación\n"
            "3. Verifica la conexión a la base de datos"
        )
        root.destroy()
        return

    # PASO 2: Validar licencia
    print("\n[2/3] Validando licencia...")
    hardware_id = generar_hardware_id()
    print(f"[*] Hardware ID: {hardware_id}")

    # Intentar leer token local
    token_local = leer_token_local()

    if token_local:
        clave, hw_id, expira = token_local
        print(f"[*] Token local encontrado: {clave}")
        print(f"[*] Expira: {expira}")

        # Validar con servidor
        print("[*] Validando con servidor...")
        if validar_licencia_con_servidor(clave, hardware_id):
            print("[OK] ✓ Licencia válida")
            global clave_licencia_global
            clave_licencia_global = clave
        else:
            print("[!] Token local inválido o expirado")
            # Pedir activación
            print("[*] Solicitando activación...")
            mostrar_activacion(on_activation_exitosa)
            return
    else:
        print("[!] No se encontró token local")
        print("[*] Solicitando activación...")
        # Mostrar pantalla de activación
        mostrar_activacion(on_activation_exitosa)
        return

    # PASO 3: Mostrar login
    print("\n[3/3] Mostrando login...")
    mostrar_login(on_login_exitoso)


if __name__ == "__main__":
    main()
