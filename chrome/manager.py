"""
Gestión de Chrome: abrir, cerrar, conectar
"""
import os
import subprocess
import psutil
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from config.settings import (
    CHROME_PROFILE,
    CHROME_DEBUG_PORT,
    CHROME_PATHS,
    DIDI_LOGIN_URL,
    log_queue
)


def cerrar_chrome_existente():
    """Cierra todas las instancias de Chrome"""
    log_queue.put("[*] Cerrando instancias previas de Chrome...")
    procesos_cerrados = 0
    for proc in psutil.process_iter(['name']):
        try:
            if 'chrome' in proc.info['name'].lower():
                proc.kill()
                procesos_cerrados += 1
        except:
            pass
    if procesos_cerrados > 0:
        log_queue.put(f"[OK] {procesos_cerrados} procesos de Chrome cerrados")
    time.sleep(2)


def reiniciar_chrome_limpio():
    """Reinicia Chrome completamente cuando hay problemas graves de contexto"""
    log_queue.put("[!] Reiniciando Chrome completamente para resolver problemas de contexto...")

    # Cerrar Chrome
    cerrar_chrome_existente()

    # Esperar a que se liberen recursos
    time.sleep(3)

    # Abrir Chrome nuevamente
    abrir_chrome_con_perfil()

    log_queue.put("[OK] Chrome reiniciado exitosamente")


def abrir_chrome_con_perfil():
    """Abre Chrome con perfil persistente y debugging (solo si no está abierto)"""
    # Verificar si Chrome ya está corriendo en el puerto 9222
    try:
        response = requests.get(f'http://localhost:{CHROME_DEBUG_PORT}/json/version', timeout=2)
        if response.status_code == 200:
            log_queue.put("[OK] Chrome ya está abierto, usando la ventana existente")
            return
    except:
        pass

    # Si no está abierto, abrirlo
    log_queue.put("[*] Abriendo Chrome con perfil dedicado...")

    os.makedirs(CHROME_PROFILE, exist_ok=True)

    chrome_exe = None
    for path in CHROME_PATHS:
        if os.path.exists(path):
            chrome_exe = path
            break

    if not chrome_exe:
        raise Exception("No se encontró Chrome instalado")

    cmd = [
        chrome_exe,
        f"--user-data-dir={CHROME_PROFILE}",
        f"--remote-debugging-port={CHROME_DEBUG_PORT}",
        DIDI_LOGIN_URL
    ]

    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    log_queue.put("[OK] Chrome abierto en pagina de login de Didi")
    time.sleep(5)


def conectar_a_chrome():
    """Se conecta a Chrome con reintentos"""
    log_queue.put("[*] Conectando al navegador...")

    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{CHROME_DEBUG_PORT}")

    driver = None
    for intento in range(3):
        try:
            driver = webdriver.Chrome(options=chrome_options)
            log_queue.put("[OK] Conectado a Chrome exitosamente")

            # Buscar y limpiar pestanas
            try:
                handles = driver.window_handles
                log_queue.put(f"[DEBUG] Encontradas {len(handles)} pestanas")

                pestana_valida = False
                pestanas_invalidas = []

                # Primero identificar pestañas válidas e inválidas
                for i, handle in enumerate(handles):
                    try:
                        driver.switch_to.window(handle)
                        _ = driver.current_url  # Test de contexto
                        log_queue.put(f"[OK] Pestana {i+1} es valida")
                        pestana_valida = True
                        break
                    except:
                        log_queue.put(f"[!] Pestana {i+1} tiene contexto perdido, marcando para cerrar...")
                        pestanas_invalidas.append(handle)
                        continue

                # Si no hay pestañas válidas, cerrar las inválidas y crear una nueva
                if not pestana_valida:
                    log_queue.put(f"[*] Cerrando {len(pestanas_invalidas)} pestanas con contexto perdido...")

                    for handle in pestanas_invalidas:
                        try:
                            driver.switch_to.window(handle)
                            driver.close()
                        except:
                            pass  # Ignorar si no se puede cerrar

                    # Abrir una nueva pestaña fresca
                    log_queue.put("[*] Abriendo nueva pestana fresca...")
                    try:
                        driver.execute_script("window.open('about:blank', '_blank');")
                        time.sleep(1)
                        driver.switch_to.window(driver.window_handles[-1])
                        log_queue.put("[OK] Nueva pestana creada y lista")
                    except Exception as e:
                        log_queue.put(f"[!] No se pudo crear nueva pestana: {str(e)}")

            except Exception as e:
                log_queue.put(f"[!] Error al gestionar pestanas: {str(e)}")

            return driver
        except:
            if intento < 2:
                log_queue.put(f"[!] Intento {intento + 1} fallido, reintentando...")
                time.sleep(3)
            else:
                raise

    return driver
