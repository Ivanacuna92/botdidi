"""
BOT DIDI - VERSIÓN CON INTERFAZ GRÁFICA
Interfaz super simple para que cualquier usuario pueda usar el bot
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import os
import sys
import requests
import subprocess
import psutil
from threading import Thread
from flask import Flask, request, jsonify
import pymysql
from datetime import datetime
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import queue
import csv
import json
from cryptography.fernet import Fernet
import base64
import hashlib

# ============================================================================
# CONFIGURACIÓN GLOBAL
# ============================================================================

CHROME_PROFILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'DidiProfile')
CREDENCIALES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.didi_creds.enc')

DB_CONFIG = {
    'host': 'datenbanken.aloia.dev',
    'port': 3306,
    'user': 'aloiaMariaDB',
    'password': 'aloiaMariaDB-17.59*2025!',
    'database': 'DidiMonitoreo',
    'charset': 'utf8mb4'
}

# Variables globales
clientes_exitosos_global = 0
bot_corriendo = False
detener_bot = False
flask_app = None
driver_global = None
codigo_2fa_input = None  # Para almacenar el código 2FA ingresado por el usuario
esperando_2fa = False

# Cola para comunicación entre threads y GUI
log_queue = queue.Queue()
stats_queue = queue.Queue()

# ============================================================================
# GESTIÓN DE CREDENCIALES ENCRIPTADAS
# ============================================================================

def generar_clave_encriptacion():
    """Genera una clave de encriptación basada en la máquina"""
    # Usamos una combinación de datos de la máquina para crear una clave única
    machine_id = os.path.dirname(os.path.abspath(__file__))
    key = hashlib.sha256(machine_id.encode()).digest()
    return base64.urlsafe_b64encode(key)

def encriptar_credenciales(usuario, password):
    """Encripta las credenciales"""
    try:
        cipher = Fernet(generar_clave_encriptacion())
        data = json.dumps({'usuario': usuario, 'password': password})
        encrypted = cipher.encrypt(data.encode())
        with open(CREDENCIALES_FILE, 'wb') as f:
            f.write(encrypted)
        return True
    except Exception as e:
        log_queue.put(f"[ERROR] No se pudieron guardar credenciales: {e}")
        return False

def desencriptar_credenciales():
    """Desencripta las credenciales guardadas"""
    try:
        if not os.path.exists(CREDENCIALES_FILE):
            return None, None

        cipher = Fernet(generar_clave_encriptacion())
        with open(CREDENCIALES_FILE, 'rb') as f:
            encrypted = f.read()

        decrypted = cipher.decrypt(encrypted)
        data = json.loads(decrypted.decode())
        return data.get('usuario'), data.get('password')
    except Exception as e:
        log_queue.put(f"[!] No se pudieron cargar credenciales guardadas: {e}")
        return None, None

def eliminar_credenciales():
    """Elimina las credenciales guardadas"""
    try:
        if os.path.exists(CREDENCIALES_FILE):
            os.remove(CREDENCIALES_FILE)
        return True
    except Exception as e:
        log_queue.put(f"[ERROR] No se pudieron eliminar credenciales: {e}")
        return False

# ============================================================================
# BACKEND FLASK INTEGRADO
# ============================================================================

def iniciar_backend():
    """Inicia el backend Flask en un hilo separado"""
    global flask_app

    flask_app = Flask(__name__)

    @flask_app.route('/registrar', methods=['POST'])
    def registrar():
        try:
            data = request.get_json()
            clientes = data.get('clientes', 0)

            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor()

            fecha_hoy = datetime.now().strftime('%Y-%m-%d')

            cursor.execute("""
                INSERT INTO bot_ejecuciones (fecha, clientes_procesados)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE
                clientes_procesados = clientes_procesados + %s
            """, (fecha_hoy, clientes, clientes))

            conn.commit()
            cursor.close()
            conn.close()

            return jsonify({'status': 'ok', 'clientes': clientes}), 200

        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @flask_app.route('/registrar_cliente', methods=['POST'])
    def registrar_cliente():
        try:
            data = request.get_json()
            nombre = data.get('nombre', 'DESCONOCIDO')
            estado = data.get('estado', 'exitoso')

            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO bot_clientes_procesados (nombre_cliente, estado)
                VALUES (%s, %s)
            """, (nombre, estado))

            conn.commit()
            cursor.close()
            conn.close()

            return jsonify({'status': 'ok', 'nombre': nombre, 'estado': estado}), 200

        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @flask_app.route('/health', methods=['GET'])
    def health():
        return jsonify({'status': 'ok'}), 200

    @flask_app.route('/estadisticas', methods=['GET'])
    def estadisticas():
        try:
            dias = int(request.args.get('dias', 7))
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            cursor.execute("""
                SELECT fecha, clientes_procesados
                FROM bot_ejecuciones
                ORDER BY fecha DESC
                LIMIT %s
            """, (dias,))

            resultados = cursor.fetchall()
            cursor.close()
            conn.close()

            return jsonify({'status': 'ok', 'datos': resultados}), 200
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    # Ejecutar Flask sin logs molestos
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    flask_app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

# ============================================================================
# GESTIÓN DE CHROME
# ============================================================================

def cerrar_chrome_existente():
    """Cierra todas las instancias de Chrome"""
    log_queue.put("[*] Cerrando instancias previas de Chrome...")
    for proc in psutil.process_iter(['name']):
        try:
            if 'chrome' in proc.info['name'].lower():
                proc.kill()
        except:
            pass
    time.sleep(2)

def abrir_chrome_con_perfil():
    """Abre Chrome con perfil persistente y debugging (solo si no está abierto)"""
    # Verificar si Chrome ya está corriendo en el puerto 9222
    try:
        response = requests.get('http://localhost:9222/json/version', timeout=2)
        if response.status_code == 200:
            log_queue.put("[OK] Chrome ya está abierto, usando la ventana existente")
            return
    except:
        pass

    # Si no está abierto, abrirlo
    log_queue.put("[*] Abriendo Chrome con perfil dedicado...")

    os.makedirs(CHROME_PROFILE, exist_ok=True)

    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
    ]

    chrome_exe = None
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_exe = path
            break

    if not chrome_exe:
        raise Exception("No se encontró Chrome instalado")

    cmd = [
        chrome_exe,
        f"--user-data-dir={CHROME_PROFILE}",
        "--remote-debugging-port=9222",
        "https://me.didiglobal.com/project/stargate-auth/html/login.html?redirect_uri=https%3A%2F%2Fmis-auth.didiglobal.com%2Fauth%3Fjumpto%3D%2F%26app_id%3D2054"
    ]

    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    log_queue.put("[OK] Chrome abierto en pagina de login de Didi")
    time.sleep(5)

def conectar_a_chrome():
    """Se conecta a Chrome con reintentos"""
    log_queue.put("[*] Conectando al navegador...")

    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    driver = None
    for intento in range(3):
        try:
            driver = webdriver.Chrome(options=chrome_options)
            log_queue.put("[OK] Conectado a Chrome exitosamente")

            # Cambiar a la última pestaña activa (la que el usuario tiene visible)
            try:
                handles = driver.window_handles
                if len(handles) > 0:
                    # Cambiar a la última pestaña (la más reciente/activa)
                    driver.switch_to.window(handles[-1])
                    log_queue.put(f"[DEBUG] Cambiado a pestaña activa ({len(handles)} pestañas abiertas)")
                    time.sleep(1)  # Dar tiempo para que cargue el contexto
            except Exception as e:
                log_queue.put(f"[!] Advertencia al cambiar pestaña: {e}")

            return driver
        except:
            if intento < 2:
                log_queue.put(f"[!] Intento {intento + 1} fallido, reintentando...")
                time.sleep(3)
            else:
                raise

def login_automatico_didi(driver, usuario, password):
    """Realiza el login automático en Didi"""
    global codigo_2fa_input, esperando_2fa

    try:
        log_queue.put("[*] Iniciando login automático...")

        # Navegar a página de login
        url_login = "https://me.didiglobal.com/project/stargate-auth/html/login.html?redirect_uri=https%3A%2F%2Fmis-auth.didiglobal.com%2Fauth%3Fjumpto%3D%2F%26app_id%3D2054"
        driver.get(url_login)
        time.sleep(3)

        # Ingresar usuario
        log_queue.put("[*] Ingresando usuario...")
        campo_usuario = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        campo_usuario.clear()
        campo_usuario.send_keys(usuario)
        time.sleep(0.5)

        # Ingresar contraseña
        log_queue.put("[*] Ingresando contraseña...")
        campo_password = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "password"))
        )
        campo_password.clear()
        campo_password.send_keys(password)
        time.sleep(0.5)

        # Click en botón de login
        log_queue.put("[*] Haciendo click en 'Iniciar sesión'...")
        boton_login = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "submit"))
        )
        boton_login.click()
        time.sleep(3)

        # Verificar si pide 2FA
        log_queue.put("[*] Verificando si se requiere 2FA...")
        try:
            campo_2fa = driver.find_element(By.ID, "sms")
            contenedor_2fa = driver.find_element(By.ID, "sms-container")

            # Verificar si el contenedor de 2FA está visible
            if contenedor_2fa.is_displayed():
                log_queue.put("[!] Se requiere código 2FA")
                log_queue.put("[!] ACCIÓN REQUERIDA: Ingresa el código 2FA en la ventana emergente")

                # Activar bandera de espera
                esperando_2fa = True
                codigo_2fa_input = None

                # Esperar hasta 120 segundos a que el usuario ingrese el código
                timeout = 120
                inicio = time.time()

                while codigo_2fa_input is None and (time.time() - inicio) < timeout:
                    time.sleep(0.5)

                if codigo_2fa_input is None:
                    log_queue.put("[ERROR] Tiempo agotado esperando código 2FA")
                    esperando_2fa = False
                    return False

                # Ingresar código 2FA
                log_queue.put(f"[*] Ingresando código 2FA...")
                campo_2fa.clear()
                campo_2fa.send_keys(codigo_2fa_input)
                time.sleep(1)

                # Click en botón de login nuevamente
                boton_login = driver.find_element(By.ID, "submit")
                boton_login.click()
                time.sleep(5)

                esperando_2fa = False
                codigo_2fa_input = None

        except:
            log_queue.put("[OK] No se requiere 2FA, continuando...")

        # Verificar si el login fue exitoso
        time.sleep(3)
        url_actual = driver.current_url

        if "/home#/index" in url_actual or "pixiu-prod.didiglobal.com" in url_actual:
            log_queue.put("[OK] Login exitoso!")
            return True
        else:
            log_queue.put(f"[!] Login falló. URL actual: {url_actual}")
            return False

    except Exception as e:
        log_queue.put(f"[ERROR] Error en login automático: {str(e)}")
        esperando_2fa = False
        return False

def verificar_sesion_didi(driver):
    """Verifica si el usuario está logueado y en la URL correcta"""
    try:
        url_esperada = "https://pixiu-prod.didiglobal.com/global-fintech/creditcard/mx/global-pixiu-api/home#/index"

        # Intentar obtener URL actual
        try:
            url_actual = driver.current_url
            log_queue.put(f"[DEBUG] URL actual: {url_actual}")
        except:
            # Si falla, navegar directamente al dashboard
            log_queue.put("[!] Contexto inválido, navegando al dashboard...")
            driver.get(url_esperada)
            time.sleep(5)  # Esperar a que cargue
            url_actual = driver.current_url
            log_queue.put(f"[DEBUG] URL después de navegar: {url_actual}")

        # Verificar URL
        if url_esperada not in url_actual and "/home#/index" not in url_actual:
            log_queue.put(f"[!] URL incorrecta. Navegando al dashboard...")
            driver.get(url_esperada)
            time.sleep(5)
            log_queue.put("[OK] Navegado al dashboard")

        log_queue.put("[OK] En dashboard correcto, verificando sesión...")

        # Verificar que el menú esté presente (usuario logueado)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//ul[@role='menubar' and contains(@class, 'el-menu')]"))
        )
        log_queue.put("[OK] Usuario logueado correctamente")
        return True
    except Exception as e:
        log_queue.put(f"[!] Error en verificación: {str(e)}")
        log_queue.put("[!] Probablemente no estés logueado o la página no cargó")
        return False

# ============================================================================
# PROCESAMIENTO DE REGISTROS
# ============================================================================

def procesar_registro(driver, indice_registro):
    """Procesa un registro completo"""
    global detener_bot

    if detener_bot:
        return False, "DETENIDO"

    try:
        log_queue.put(f"[*] Procesando registro #{indice_registro + 1}")

        time.sleep(1)

        botones_detalles = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//td[not(contains(@class, 'is-hidden'))]//button[contains(@class, 'el-button') and .//span[text()='Detalles']]"))
        )

        if indice_registro >= len(botones_detalles):
            return False, "SIN_REGISTROS"

        boton_detalles = botones_detalles[indice_registro]

        # Capturar el nombre del cliente antes de hacer click
        try:
            fila = boton_detalles.find_element(By.XPATH, "./ancestor::tr")
            # Intentar diferentes estrategias para encontrar el nombre
            nombre_cliente = "DESCONOCIDO"

            # Estrategia 1: Buscar directamente la columna 4
            try:
                col4 = fila.find_element(By.XPATH, ".//td[contains(@class, 'el-table_1_column_4')]//div[@class='cell']")
                nombre_cliente = col4.text.strip()
            except:
                pass

            # Estrategia 2: Si no funcionó, buscar cualquier celda con formato de nombre (con comas)
            if nombre_cliente == "DESCONOCIDO":
                columnas = fila.find_elements(By.XPATH, ".//td[contains(@class, 'is-center')]//div[@class='cell']")
                for col in columnas:
                    texto = col.text.strip()
                    # Los nombres tienen formato: NOMBRE,APELLIDO1,APELLIDO2
                    if texto and texto.count(',') >= 2:
                        nombre_cliente = texto
                        break

            log_queue.put(f"[OK] Cliente: {nombre_cliente}")
        except Exception as e:
            nombre_cliente = "DESCONOCIDO"
            log_queue.put(f"[!] Error al capturar nombre: {str(e)}")

        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", boton_detalles)
        time.sleep(0.5)

        try:
            boton_detalles.click()
        except:
            driver.execute_script("arguments[0].click();", boton_detalles)

        time.sleep(2)

        # Verificar si se debe detener
        if detener_bot:
            log_queue.put("[!] Bot detenido por el usuario")
            return False, nombre_cliente

        # WhatsApp
        boton_whatsapp = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'el-button') and contains(., 'whatsapp')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", boton_whatsapp)
        time.sleep(0.5)
        try:
            boton_whatsapp.click()
        except:
            driver.execute_script("arguments[0].click();", boton_whatsapp)
        time.sleep(2)

        # Verificar si se debe detener
        if detener_bot:
            log_queue.put("[!] Bot detenido por el usuario")
            return False, nombre_cliente

        # Plantilla
        boton_plantilla = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'check-template80')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", boton_plantilla)
        time.sleep(0.5)
        try:
            boton_plantilla.click()
        except:
            driver.execute_script("arguments[0].click();", boton_plantilla)
        time.sleep(2)

        # Enviar
        contenido_plantilla = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'wa-template-content')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", contenido_plantilla)
        time.sleep(0.5)
        try:
            contenido_plantilla.click()
        except:
            driver.execute_script("arguments[0].click();", contenido_plantilla)
        time.sleep(1.5)

        botones = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//button[@type='button' and contains(@class, 'el-button--primary') and contains(@class, 'el-button--medium')]"))
        )
        boton_enviar = None
        for boton in botones:
            if "Enviar" in boton.text:
                boton_enviar = boton
                break

        if boton_enviar:
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", boton_enviar)
            time.sleep(0.5)
            try:
                boton_enviar.click()
            except:
                driver.execute_script("arguments[0].click();", boton_enviar)
            time.sleep(2)

        # Verificar si se debe detener
        if detener_bot:
            log_queue.put("[!] Bot detenido por el usuario")
            return False, nombre_cliente

        # Código del pago
        time.sleep(2)
        botones = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//button[@type='button' and contains(@class, 'el-button--primary') and contains(@class, 'el-button--mini')]"))
        )
        boton_codigo = None
        for boton in botones:
            if "Código del pago" in boton.text or "Codigo del pago" in boton.text:
                boton_codigo = boton
                break

        if boton_codigo:
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", boton_codigo)
            time.sleep(0.5)
            try:
                boton_codigo.click()
            except:
                driver.execute_script("arguments[0].click();", boton_codigo)
            time.sleep(2)

        # Verificar si se debe detener
        if detener_bot:
            log_queue.put("[!] Bot detenido por el usuario")
            return False, nombre_cliente

        # Confirmar
        time.sleep(1)
        radio_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//table//input[@type='radio']"))
        )
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", radio_button)
        time.sleep(0.5)
        try:
            radio_button.click()
        except:
            driver.execute_script("arguments[0].click();", radio_button)
        time.sleep(1.5)

        botones_confirmar = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//button[@type='button' and contains(@class, 'el-button--primary') and contains(@class, 'el-button--medium')]"))
        )
        boton_confirmar = None
        for boton in botones_confirmar:
            if "Confirmar" in boton.text:
                boton_confirmar = boton
                break

        if boton_confirmar:
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", boton_confirmar)
            time.sleep(0.5)
            try:
                boton_confirmar.click()
            except:
                driver.execute_script("arguments[0].click();", boton_confirmar)
            time.sleep(2)

        # Cerrar pestaña
        try:
            boton_cerrar_tab = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//span[contains(@class, 'tags-view-item') and contains(., 'Detalles del lead')]//span[contains(@class, 'el-icon-close')]"))
            )
            try:
                boton_cerrar_tab.click()
            except:
                driver.execute_script("arguments[0].click();", boton_cerrar_tab)
            time.sleep(1)
        except:
            link_mis_casos = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//a[@href='/pixiu/#/my_case/my_case_index']//li[@class='el-menu-item']"))
            )
            try:
                link_mis_casos.click()
            except:
                driver.execute_script("arguments[0].click();", link_mis_casos)
            time.sleep(2)

        log_queue.put(f"[OK] Registro #{indice_registro + 1} completado - {nombre_cliente}")
        return True, nombre_cliente

    except Exception as e:
        nombre_cliente = locals().get('nombre_cliente', 'DESCONOCIDO')
        log_queue.put(f"[ERROR] Error en registro #{indice_registro + 1}: {str(e)}")
        try:
            link_mis_casos = driver.find_element(By.XPATH, "//a[@href='/pixiu/#/my_case/my_case_index']//li[@class='el-menu-item']")
            driver.execute_script("arguments[0].click();", link_mis_casos)
            time.sleep(2)
        except:
            pass
        return False, nombre_cliente

# ============================================================================
# NAVEGACIÓN Y PROCESAMIENTO PRINCIPAL
# ============================================================================

def navegar_a_mis_casos(driver):
    """Navega al menú Mis casos"""
    log_queue.put("[*] Navegando al dashboard...")

    # Menu principal
    menu_principal = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//ul[@role='menubar' and contains(@class, 'el-menu')]"))
    )

    # Expandir Mesa de trabajo
    submenu_mesa_trabajo = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//div[@class='el-submenu__title']//span[contains(@title, 'Mesa de trabajo')]"))
    )
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", submenu_mesa_trabajo)
    time.sleep(0.5)
    try:
        submenu_mesa_trabajo.click()
    except:
        driver.execute_script("arguments[0].click();", submenu_mesa_trabajo)
    time.sleep(1.5)

    # Expandir Mis casos
    submenu_mis_casos = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//div[@class='nest-menu']//div[@class='el-submenu__title']//span[@title='Mis casos']"))
    )
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", submenu_mis_casos)
    time.sleep(0.5)
    try:
        submenu_mis_casos.click()
    except:
        driver.execute_script("arguments[0].click();", submenu_mis_casos)
    time.sleep(1.5)

    # Click en link final
    link_mis_casos = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//a[@href='/pixiu/#/my_case/my_case_index']//li[@class='el-menu-item']"))
    )
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", link_mis_casos)
    time.sleep(0.5)
    try:
        link_mis_casos.click()
    except:
        driver.execute_script("arguments[0].click();", link_mis_casos)
    time.sleep(2)

    log_queue.put("[OK] Navegación completada")

def ejecutar_bot(credenciales=None):
    """Función principal del bot (se ejecuta en thread separado)"""
    global clientes_exitosos_global, bot_corriendo, detener_bot, driver_global

    bot_corriendo = True
    detener_bot = False
    clientes_exitosos_global = 0

    total_procesados = 0
    total_exitosos = 0
    total_errores = 0
    pagina_actual = 1

    try:
        # 1. Iniciar backend
        log_queue.put("[*] Iniciando backend...")
        backend_thread = Thread(target=iniciar_backend, daemon=True)
        backend_thread.start()
        time.sleep(2)
        log_queue.put("[OK] Backend iniciado")

        # 2. Gestionar Chrome
        # No cerramos otras instancias porque usamos un perfil independiente
        abrir_chrome_con_perfil()

        # 3. Conectar
        driver = conectar_a_chrome()
        driver_global = driver

        # 4. Verificar sesión y URL, o hacer login automático
        sesion_activa = verificar_sesion_didi(driver)

        if not sesion_activa:
            # Si no hay sesión activa, intentar login automático si se proporcionaron credenciales
            if credenciales:
                usuario, password = credenciales
                log_queue.put("[*] No hay sesión activa, intentando login automático...")

                if login_automatico_didi(driver, usuario, password):
                    log_queue.put("[OK] Login automático exitoso!")
                    sesion_activa = True
                else:
                    log_queue.put("[ERROR] Login automático falló")
                    log_queue.put("[!] ACCIÓN REQUERIDA:")
                    log_queue.put("[!] 1. Ve a Chrome y verifica las credenciales")
                    log_queue.put("[!] 2. Loguéate manualmente si es necesario")
                    log_queue.put("[!] 3. Presiona INICIAR nuevamente cuando estés listo")
                    bot_corriendo = False
                    return
            else:
                # No hay credenciales, pedir login manual
                log_queue.put("[!] ACCIÓN REQUERIDA:")
                log_queue.put("[!] 1. Ve a Chrome y loguéate en Didi")
                log_queue.put("[!] 2. Navega a la página principal (Dashboard)")
                log_queue.put("[!] 3. Presiona INICIAR nuevamente cuando estés listo")
                bot_corriendo = False
                return

        # 5. Navegar
        navegar_a_mis_casos(driver)

        # 6. Procesar registros
        log_queue.put("[*] Iniciando procesamiento masivo...")

        while not detener_bot:
            log_queue.put(f"[*] Procesando página {pagina_actual}...")

            tabla = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//table[contains(@class, 'el-table')]"))
            )
            time.sleep(1)

            botones_detalles = driver.find_elements(By.XPATH, "//td[not(contains(@class, 'is-hidden'))]//button[contains(@class, 'el-button') and .//span[text()='Detalles']]")
            num_registros = len(botones_detalles)
            log_queue.put(f"[OK] {num_registros} registros en página {pagina_actual}")

            if num_registros == 0:
                break

            for i in range(num_registros):
                if detener_bot:
                    break

                total_procesados += 1
                exito, nombre_cliente = procesar_registro(driver, i)

                # Registrar cliente individual en la base de datos
                if exito:
                    total_exitosos += 1
                    clientes_exitosos_global += 1
                    # Registrar cliente individual Y actualizar contador diario
                    try:
                        r1 = requests.post('http://localhost:5000/registrar_cliente',
                                    json={'nombre': nombre_cliente, 'estado': 'exitoso'},
                                    timeout=2)
                        if r1.status_code != 200:
                            log_queue.put(f"[!] Error al registrar cliente: {r1.text}")
                        # Actualizar contador diario también
                        r2 = requests.post('http://localhost:5000/registrar',
                                    json={'clientes': 1},
                                    timeout=2)
                        if r2.status_code != 200:
                            log_queue.put(f"[!] Error al actualizar contador: {r2.text}")
                    except Exception as e:
                        log_queue.put(f"[!] Error guardando en BD: {e}")
                    stats_queue.put({
                        'total': total_procesados,
                        'exitosos': total_exitosos,
                        'errores': total_errores,
                        'pagina': pagina_actual
                    })
                else:
                    total_errores += 1
                    # Registrar solo cliente individual (errores no se cuentan en bot_ejecuciones)
                    try:
                        r1 = requests.post('http://localhost:5000/registrar_cliente',
                                    json={'nombre': nombre_cliente, 'estado': 'error'},
                                    timeout=2)
                        if r1.status_code != 200:
                            log_queue.put(f"[!] Error al registrar cliente con error: {r1.text}")
                    except Exception as e:
                        log_queue.put(f"[!] Error guardando cliente con error en BD: {e}")
                    stats_queue.put({
                        'total': total_procesados,
                        'exitosos': total_exitosos,
                        'errores': total_errores,
                        'pagina': pagina_actual
                    })

            if detener_bot:
                break

            # Siguiente página
            try:
                boton_siguiente = driver.find_element(By.XPATH, "//button[contains(@class, 'btn-next') and not(@disabled)]//i[contains(@class, 'el-icon-arrow-right')]")
                boton_siguiente_padre = boton_siguiente.find_element(By.XPATH, "./..")
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", boton_siguiente_padre)
                time.sleep(0.5)
                try:
                    boton_siguiente_padre.click()
                except:
                    driver.execute_script("arguments[0].click();", boton_siguiente_padre)
                time.sleep(2)
                pagina_actual += 1
            except:
                log_queue.put("[OK] No hay más páginas")
                break

        # Guardar en BD
        if clientes_exitosos_global > 0 and not detener_bot:
            log_queue.put(f"[*] Guardando {clientes_exitosos_global} clientes en BD...")
            try:
                response = requests.post('http://localhost:5000/registrar',
                                        json={'clientes': clientes_exitosos_global},
                                        timeout=5)
                if response.status_code == 200:
                    log_queue.put(f"[OK] {clientes_exitosos_global} clientes guardados")
            except Exception as e:
                log_queue.put(f"[ERROR] No se pudo guardar: {e}")

        if detener_bot:
            log_queue.put("[!] Bot detenido por el usuario")
        else:
            log_queue.put("[OK] PROCESAMIENTO COMPLETADO")
            log_queue.put(f"[*] Total: {total_procesados} | Exitosos: {total_exitosos} | Errores: {total_errores}")

    except Exception as e:
        log_queue.put(f"[ERROR] Error crítico: {str(e)}")
        import traceback
        log_queue.put(traceback.format_exc())

    finally:
        bot_corriendo = False
        driver_global = None

# ============================================================================
# INTERFAZ GRÁFICA CON TKINTER
# ============================================================================

class BotDidiGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 Bot Didi - Sistema Automatizado")
        self.root.geometry("700x750")
        self.root.resizable(True, True)

        # Configurar estilo
        style = ttk.Style()
        style.theme_use('clam')

        # Variables
        self.estado_var = tk.StringVar(value="LISTO")
        self.clientes_var = tk.StringVar(value="0")
        self.exitosos_var = tk.StringVar(value="0")
        self.errores_var = tk.StringVar(value="0")
        self.pagina_var = tk.StringVar(value="0")

        # Variables de credenciales
        self.usuario_var = tk.StringVar(value="")
        self.password_var = tk.StringVar(value="")
        self.guardar_creds_var = tk.BooleanVar(value=False)
        self.usar_login_auto_var = tk.BooleanVar(value=False)

        self.crear_interfaz()

        # Cargar credenciales guardadas si existen
        self.cargar_credenciales_guardadas()

        # Iniciar actualización del log
        self.actualizar_log()
        self.actualizar_stats()
        self.verificar_2fa_pendiente()

    def crear_interfaz(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Título
        titulo = tk.Label(main_frame, text="🤖 BOT DIDI", font=("Arial", 20, "bold"), fg="#2C3E50")
        titulo.pack(pady=10)

        # === SECCIÓN DE LOGIN AUTOMÁTICO ===
        login_frame = ttk.LabelFrame(main_frame, text="🔐 Login Automático (Opcional)", padding="10")
        login_frame.pack(fill=tk.X, pady=10)

        # Checkbox para activar/desactivar login automático
        check_login_auto = ttk.Checkbutton(login_frame, text="Usar login automático",
                                           variable=self.usar_login_auto_var,
                                           command=self.toggle_campos_login)
        check_login_auto.pack(anchor=tk.W, pady=5)

        # Frame para campos de login (inicialmente deshabilitado)
        self.campos_login_frame = ttk.Frame(login_frame)
        self.campos_login_frame.pack(fill=tk.X, pady=5)

        # Usuario
        user_frame = ttk.Frame(self.campos_login_frame)
        user_frame.pack(fill=tk.X, pady=3)
        tk.Label(user_frame, text="Usuario:", font=("Arial", 9), width=10, anchor=tk.W).pack(side=tk.LEFT)
        self.entry_usuario = ttk.Entry(user_frame, textvariable=self.usuario_var, width=30, state=tk.DISABLED)
        self.entry_usuario.pack(side=tk.LEFT, padx=5)

        # Contraseña
        pass_frame = ttk.Frame(self.campos_login_frame)
        pass_frame.pack(fill=tk.X, pady=3)
        tk.Label(pass_frame, text="Contraseña:", font=("Arial", 9), width=10, anchor=tk.W).pack(side=tk.LEFT)
        self.entry_password = ttk.Entry(pass_frame, textvariable=self.password_var, show="*", width=30, state=tk.DISABLED)
        self.entry_password.pack(side=tk.LEFT, padx=5)

        # Opciones
        opciones_frame = ttk.Frame(self.campos_login_frame)
        opciones_frame.pack(fill=tk.X, pady=5)

        self.check_guardar_creds = ttk.Checkbutton(opciones_frame, text="Guardar credenciales (encriptadas)",
                                                   variable=self.guardar_creds_var, state=tk.DISABLED)
        self.check_guardar_creds.pack(side=tk.LEFT, padx=5)

        self.btn_eliminar_creds = tk.Button(opciones_frame, text="🗑️ Borrar guardadas",
                                           font=("Arial", 8),
                                           bg="#E74C3C", fg="white",
                                           command=self.eliminar_credenciales_guardadas,
                                           state=tk.DISABLED)
        self.btn_eliminar_creds.pack(side=tk.LEFT, padx=5)

        # Estado
        estado_frame = ttk.Frame(main_frame)
        estado_frame.pack(fill=tk.X, pady=5)

        tk.Label(estado_frame, text="Estado:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.estado_label = tk.Label(estado_frame, textvariable=self.estado_var,
                                     font=("Arial", 10), fg="#27AE60")
        self.estado_label.pack(side=tk.LEFT, padx=10)

        # Botones de control
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=15)

        self.btn_iniciar = tk.Button(btn_frame, text="▶  INICIAR BOT",
                                     font=("Arial", 14, "bold"),
                                     bg="#27AE60", fg="white",
                                     width=20, height=2,
                                     command=self.iniciar_bot)
        self.btn_iniciar.pack(side=tk.LEFT, padx=5)

        self.btn_detener = tk.Button(btn_frame, text="⬛  DETENER",
                                     font=("Arial", 14, "bold"),
                                     bg="#E74C3C", fg="white",
                                     width=15, height=2,
                                     command=self.detener_bot,
                                     state=tk.DISABLED)
        self.btn_detener.pack(side=tk.LEFT, padx=5)

        # Estadísticas
        stats_frame = ttk.LabelFrame(main_frame, text="📊 Estadísticas en Vivo", padding="10")
        stats_frame.pack(fill=tk.X, pady=10)

        # Grid de estadísticas
        tk.Label(stats_frame, text="Clientes procesados:", font=("Arial", 9)).grid(row=0, column=0, sticky=tk.W, pady=2)
        tk.Label(stats_frame, textvariable=self.clientes_var, font=("Arial", 9, "bold"), fg="#3498DB").grid(row=0, column=1, sticky=tk.W, padx=10)

        tk.Label(stats_frame, text="Exitosos:", font=("Arial", 9)).grid(row=1, column=0, sticky=tk.W, pady=2)
        tk.Label(stats_frame, textvariable=self.exitosos_var, font=("Arial", 9, "bold"), fg="#27AE60").grid(row=1, column=1, sticky=tk.W, padx=10)

        tk.Label(stats_frame, text="Errores:", font=("Arial", 9)).grid(row=2, column=0, sticky=tk.W, pady=2)
        tk.Label(stats_frame, textvariable=self.errores_var, font=("Arial", 9, "bold"), fg="#E74C3C").grid(row=2, column=1, sticky=tk.W, padx=10)

        tk.Label(stats_frame, text="Página actual:", font=("Arial", 9)).grid(row=3, column=0, sticky=tk.W, pady=2)
        tk.Label(stats_frame, textvariable=self.pagina_var, font=("Arial", 9, "bold"), fg="#8E44AD").grid(row=3, column=1, sticky=tk.W, padx=10)

        # Log
        log_frame = ttk.LabelFrame(main_frame, text="📝 Log de Actividad", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, state=tk.DISABLED,
                                                  font=("Consolas", 9), bg="#2C3E50", fg="#ECF0F1")
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Botones de reportes
        reportes_frame = ttk.Frame(main_frame)
        reportes_frame.pack(pady=5)

        btn_stats = tk.Button(reportes_frame, text="📊 Ver Estadísticas Completas",
                             font=("Arial", 10),
                             bg="#3498DB", fg="white",
                             command=self.ver_estadisticas)
        btn_stats.pack(side=tk.LEFT, padx=5)

        btn_reporte = tk.Button(reportes_frame, text="💾 Descargar Reporte CSV",
                               font=("Arial", 10),
                               bg="#9B59B6", fg="white",
                               command=self.generar_reporte)
        btn_reporte.pack(side=tk.LEFT, padx=5)

    def agregar_log(self, mensaje):
        """Agrega mensaje al log"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, mensaje + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def actualizar_log(self):
        """Actualiza el log desde la cola"""
        try:
            while True:
                mensaje = log_queue.get_nowait()
                self.agregar_log(mensaje)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.actualizar_log)

    def actualizar_stats(self):
        """Actualiza las estadísticas desde la cola"""
        try:
            while True:
                stats = stats_queue.get_nowait()
                self.clientes_var.set(str(stats['total']))
                self.exitosos_var.set(str(stats['exitosos']))
                self.errores_var.set(str(stats['errores']))
                self.pagina_var.set(str(stats['pagina']))
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.actualizar_stats)

    def iniciar_bot(self):
        """Inicia el bot en un thread separado"""
        global bot_corriendo

        if bot_corriendo:
            messagebox.showwarning("Bot en ejecución", "El bot ya está corriendo")
            return

        # Verificar si se debe usar login automático
        usar_login_auto = self.usar_login_auto_var.get()
        usuario = self.usuario_var.get().strip()
        password = self.password_var.get().strip()

        if usar_login_auto:
            if not usuario or not password:
                messagebox.showerror("Error", "Debes ingresar usuario y contraseña para usar login automático")
                return

            # Guardar credenciales si el usuario lo solicitó
            if self.guardar_creds_var.get():
                if encriptar_credenciales(usuario, password):
                    log_queue.put("[OK] Credenciales guardadas de forma segura")

        self.estado_var.set("PROCESANDO")
        self.estado_label.config(fg="#E67E22")
        self.btn_iniciar.config(state=tk.DISABLED)
        self.btn_detener.config(state=tk.NORMAL)

        # Pasar credenciales al bot si está habilitado
        credenciales = (usuario, password) if usar_login_auto else None

        # Iniciar bot en thread
        bot_thread = Thread(target=ejecutar_bot, args=(credenciales,), daemon=True)
        bot_thread.start()

        # Verificar cuando termine
        self.verificar_estado_bot()

    def detener_bot(self):
        """Detiene el bot"""
        global detener_bot

        respuesta = messagebox.askyesno("Detener Bot",
                                        "¿Estás seguro de que quieres detener el bot?")
        if respuesta:
            detener_bot = True
            log_queue.put("[!] Deteniendo bot...")

    def verificar_estado_bot(self):
        """Verifica el estado del bot periódicamente"""
        global bot_corriendo

        if not bot_corriendo:
            self.estado_var.set("LISTO")
            self.estado_label.config(fg="#27AE60")
            self.btn_iniciar.config(state=tk.NORMAL)
            self.btn_detener.config(state=tk.DISABLED)
        else:
            self.root.after(1000, self.verificar_estado_bot)

    def ver_estadisticas(self):
        """Muestra ventana con estadísticas completas"""
        try:
            response = requests.get('http://localhost:5000/estadisticas?dias=30', timeout=5)
            if response.status_code == 200:
                datos = response.json()['datos']

                # Crear ventana de estadísticas
                stats_window = tk.Toplevel(self.root)
                stats_window.title("Estadísticas Completas (últimos 30 días)")
                stats_window.geometry("500x400")

                # Tabla de estadísticas
                tree = ttk.Treeview(stats_window, columns=('Fecha', 'Clientes'), show='headings')
                tree.heading('Fecha', text='Fecha')
                tree.heading('Clientes', text='Clientes Procesados')

                tree.column('Fecha', width=200)
                tree.column('Clientes', width=200)

                for dato in datos:
                    tree.insert('', tk.END, values=(dato['fecha'], dato['clientes_procesados']))

                tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            else:
                messagebox.showerror("Error", "No se pudieron obtener las estadísticas")
        except Exception as e:
            messagebox.showerror("Error", f"Backend no disponible: {e}")

    def generar_reporte(self):
        """Genera y descarga un reporte CSV de clientes procesados hoy"""
        try:
            # Obtener clientes procesados hoy desde el backend
            response = requests.get('http://localhost:5000/clientes_hoy', timeout=5)
            if response.status_code != 200:
                messagebox.showerror("Error", "No se pudieron obtener los datos del reporte")
                return

            datos = response.json()
            clientes = datos.get('clientes', [])
            total = datos.get('total', 0)
            exitosos = datos.get('exitosos', 0)
            errores = datos.get('errores', 0)

            if total == 0:
                messagebox.showinfo("Reporte", "No hay clientes procesados hoy para generar reporte")
                return

            # Pedir al usuario dónde guardar el archivo
            fecha_hoy = datetime.now().strftime('%Y-%m-%d')
            archivo_default = f"Reporte_Clientes_{fecha_hoy}.csv"

            archivo = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=archivo_default,
                title="Guardar Reporte"
            )

            if not archivo:  # Usuario canceló
                return

            # Crear el archivo CSV
            with open(archivo, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)

                # Encabezado del reporte
                writer.writerow(['REPORTE DE CLIENTES PROCESADOS'])
                writer.writerow(['Fecha', fecha_hoy])
                writer.writerow(['Total de clientes', total])
                writer.writerow(['Exitosos', exitosos])
                writer.writerow(['Errores', errores])
                writer.writerow([])  # Línea en blanco

                # Encabezados de la tabla
                writer.writerow(['ID', 'Nombre del Cliente', 'Estado', 'Fecha/Hora Procesado'])

                # Datos de clientes
                for cliente in clientes:
                    writer.writerow([
                        cliente['id'],
                        cliente['nombre_cliente'],
                        cliente['estado'].upper(),
                        cliente['fecha_procesado']
                    ])

            messagebox.showinfo("Éxito", f"Reporte generado exitosamente:\n{archivo}\n\nTotal: {total} clientes ({exitosos} exitosos, {errores} errores)")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el reporte: {e}")

    # ========================================================================
    # MÉTODOS PARA LOGIN AUTOMÁTICO
    # ========================================================================

    def toggle_campos_login(self):
        """Habilita/deshabilita los campos de login según el checkbox"""
        if self.usar_login_auto_var.get():
            self.entry_usuario.config(state=tk.NORMAL)
            self.entry_password.config(state=tk.NORMAL)
            self.check_guardar_creds.config(state=tk.NORMAL)
            self.btn_eliminar_creds.config(state=tk.NORMAL)
        else:
            self.entry_usuario.config(state=tk.DISABLED)
            self.entry_password.config(state=tk.DISABLED)
            self.check_guardar_creds.config(state=tk.DISABLED)
            self.btn_eliminar_creds.config(state=tk.DISABLED)

    def cargar_credenciales_guardadas(self):
        """Carga las credenciales guardadas si existen"""
        usuario, password = desencriptar_credenciales()
        if usuario and password:
            self.usuario_var.set(usuario)
            self.password_var.set(password)
            self.guardar_creds_var.set(True)
            self.usar_login_auto_var.set(True)
            self.toggle_campos_login()
            log_queue.put("[OK] Credenciales cargadas desde archivo guardado")

    def eliminar_credenciales_guardadas(self):
        """Elimina las credenciales guardadas"""
        respuesta = messagebox.askyesno("Eliminar Credenciales",
                                        "¿Estás seguro de que quieres eliminar las credenciales guardadas?")
        if respuesta:
            if eliminar_credenciales():
                self.usuario_var.set("")
                self.password_var.set("")
                self.guardar_creds_var.set(False)
                messagebox.showinfo("Éxito", "Credenciales eliminadas correctamente")
                log_queue.put("[OK] Credenciales eliminadas")

    def verificar_2fa_pendiente(self):
        """Verifica periódicamente si hay solicitud de 2FA pendiente"""
        global esperando_2fa, codigo_2fa_input

        if esperando_2fa and codigo_2fa_input is None:
            # Mostrar modal para ingresar código 2FA
            self.mostrar_modal_2fa()

        # Revisar cada segundo
        self.root.after(1000, self.verificar_2fa_pendiente)

    def mostrar_modal_2fa(self):
        """Muestra modal para que el usuario ingrese el código 2FA"""
        global codigo_2fa_input, esperando_2fa

        # Evitar abrir múltiples modales
        if hasattr(self, 'modal_2fa_abierto') and self.modal_2fa_abierto:
            return

        self.modal_2fa_abierto = True

        # Crear ventana modal
        modal = tk.Toplevel(self.root)
        modal.title("🔐 Código 2FA Requerido")
        modal.geometry("400x200")
        modal.resizable(False, False)
        modal.grab_set()  # Modal

        # Centrar ventana
        modal.transient(self.root)

        # Contenido
        frame = ttk.Frame(modal, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Se requiere código de verificación 2FA",
                font=("Arial", 12, "bold")).pack(pady=10)

        tk.Label(frame, text="Ingresa el código que recibiste:",
                font=("Arial", 10)).pack(pady=5)

        codigo_var = tk.StringVar()
        entry_codigo = ttk.Entry(frame, textvariable=codigo_var,
                                font=("Arial", 14), width=15, justify=tk.CENTER)
        entry_codigo.pack(pady=10)
        entry_codigo.focus()

        def confirmar_codigo():
            global codigo_2fa_input
            codigo = codigo_var.get().strip()
            if len(codigo) == 6 and codigo.isdigit():
                codigo_2fa_input = codigo
                self.modal_2fa_abierto = False
                modal.destroy()
                log_queue.put(f"[OK] Código 2FA recibido")
            else:
                messagebox.showerror("Error", "El código debe tener 6 dígitos numéricos")

        def cancelar():
            global esperando_2fa
            esperando_2fa = False
            self.modal_2fa_abierto = False
            modal.destroy()
            log_queue.put("[!] Login 2FA cancelado por el usuario")

        # Botones
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="✓ Confirmar", font=("Arial", 10, "bold"),
                 bg="#27AE60", fg="white", width=12,
                 command=confirmar_codigo).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="✗ Cancelar", font=("Arial", 10),
                 bg="#E74C3C", fg="white", width=12,
                 command=cancelar).pack(side=tk.LEFT, padx=5)

        # Bind Enter key
        entry_codigo.bind('<Return>', lambda e: confirmar_codigo())

        # Al cerrar la ventana
        modal.protocol("WM_DELETE_WINDOW", cancelar)

# ============================================================================
# MAIN
# ============================================================================

def main():
    root = tk.Tk()
    app = BotDidiGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
