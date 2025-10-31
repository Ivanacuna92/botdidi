"""
Lógica principal de ejecución del bot
"""
import time
import psutil
import requests
from threading import Thread
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import config.settings as settings
from config.settings import log_queue, stats_queue
from backend.flask_server import iniciar_backend
from chrome.manager import abrir_chrome_con_perfil, conectar_a_chrome
from chrome.session import verificar_sesion_didi
from bot.navigator import navegar_a_mis_casos
from bot.processor import procesar_registro


def ejecutar_bot(token):
    """Función principal del bot (se ejecuta en thread separado)"""
    settings.bot_corriendo = True
    settings.detener_bot = False
    settings.clientes_exitosos_global = 0

    total_procesados = 0
    total_exitosos = 0
    total_errores = 0
    pagina_actual = 1

    # Headers de autenticación para todas las peticiones
    headers = {'Authorization': f'Bearer {token}'}

    try:
        # 1. Verificar que el backend esté disponible (ya está corriendo desde el inicio)
        log_queue.put("[*] Verificando conexión con backend...")
        backend_ok = False
        try:
            response = requests.get('http://localhost:5000/health', timeout=3)
            if response.status_code == 200:
                log_queue.put("[OK] Backend disponible")
                backend_ok = True
        except Exception as e:
            log_queue.put(f"[ERROR] Backend no disponible: {str(e)}")
            settings.bot_corriendo = False
            return

        if not backend_ok:
            log_queue.put("[ERROR] El bot no puede continuar sin backend")
            settings.bot_corriendo = False
            return

        # 2. Gestionar Chrome
        # No cerramos otras instancias porque usamos un perfil independiente
        abrir_chrome_con_perfil()

        # 3. Conectar
        driver = conectar_a_chrome()
        settings.driver_global = driver

        # 4. Verificar sesión y URL con espera inteligente
        log_queue.put("[*] Verificando sesión...")
        sesion_valida = verificar_sesion_didi(driver)

        if not sesion_valida:
            log_queue.put("[!] No se detectó sesión activa")
            log_queue.put("[*] Esperando a que te loguees en Chrome...")
            log_queue.put("[*] Tienes 5 minutos para completar el login")
            log_queue.put("[!] ACCIÓN REQUERIDA:")
            log_queue.put("[!] 1. Ve a la ventana de Chrome")
            log_queue.put("[!] 2. Completa el login en Didi")
            log_queue.put("[!] 3. El bot detectará automáticamente cuando termines")

            # Loop de espera: 30 intentos × 10 segundos = 5 minutos
            intentos_maximos = 30
            for intento in range(intentos_maximos):
                if settings.detener_bot:
                    log_queue.put("[!] Espera de login cancelada por el usuario")
                    settings.bot_corriendo = False
                    return

                time.sleep(10)  # Esperar 10 segundos entre intentos

                tiempo_restante = (intentos_maximos - intento - 1) * 10
                minutos = tiempo_restante // 60
                segundos = tiempo_restante % 60

                log_queue.put(f"[*] Verificando login... (Intento {intento + 1}/{intentos_maximos} - Quedan {minutos}m {segundos}s)")

                if verificar_sesion_didi(driver):
                    log_queue.put("[OK] ✓ Login detectado exitosamente!")
                    sesion_valida = True
                    break

            if not sesion_valida:
                log_queue.put("[ERROR] Tiempo agotado esperando login (5 minutos)")
                log_queue.put("[!] Por favor loguéate manualmente y presiona INICIAR nuevamente")
                settings.bot_corriendo = False
                return

        # 5. Navegar
        navegar_a_mis_casos(driver)

        # 6. Procesar registros
        log_queue.put("[*] Iniciando procesamiento masivo...")

        while not settings.detener_bot:
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
                if settings.detener_bot:
                    break

                total_procesados += 1
                exito, datos_cliente = procesar_registro(driver, i)

                # Registrar cliente individual en la base de datos
                if exito:
                    total_exitosos += 1
                    settings.clientes_exitosos_global += 1
                    # Registrar cliente individual Y actualizar contador diario
                    try:
                        r1 = requests.post('http://localhost:5000/registrar_cliente',
                                    headers=headers,
                                    json={
                                        'nombre': datos_cliente['nombre'],
                                        'cfrnid': datos_cliente['cfrnid'],
                                        'monto_total': datos_cliente['monto_total'],
                                        'estado': 'exitoso'
                                    },
                                    timeout=10)
                        if r1.status_code != 200:
                            log_queue.put(f"[!] Error al registrar cliente: {r1.text}")
                        # Actualizar contador diario también
                        r2 = requests.post('http://localhost:5000/registrar',
                                    headers=headers,
                                    json={'clientes': 1, 'exitosos': 1, 'errores': 0},
                                    timeout=10)
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
                    # Registrar cliente individual y contador de errores
                    try:
                        r1 = requests.post('http://localhost:5000/registrar_cliente',
                                    headers=headers,
                                    json={
                                        'nombre': datos_cliente['nombre'],
                                        'cfrnid': datos_cliente['cfrnid'],
                                        'monto_total': datos_cliente['monto_total'],
                                        'estado': 'error'
                                    },
                                    timeout=10)
                        if r1.status_code != 200:
                            log_queue.put(f"[!] Error al registrar cliente con error: {r1.text}")
                        # Registrar error en contador diario
                        r2 = requests.post('http://localhost:5000/registrar',
                                    headers=headers,
                                    json={'clientes': 1, 'exitosos': 0, 'errores': 1},
                                    timeout=10)
                        if r2.status_code != 200:
                            log_queue.put(f"[!] Error al actualizar contador: {r2.text}")
                    except Exception as e:
                        log_queue.put(f"[!] Error guardando cliente con error en BD: {e}")
                    stats_queue.put({
                        'total': total_procesados,
                        'exitosos': total_exitosos,
                        'errores': total_errores,
                        'pagina': pagina_actual
                    })

            if settings.detener_bot:
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

        # Ya no es necesario guardar al final porque se guarda en cada registro procesado
        # Este código se mantiene por compatibilidad pero ya no hace falta

        if settings.detener_bot:
            log_queue.put("[!] Bot detenido por el usuario")
        else:
            log_queue.put("[OK] PROCESAMIENTO COMPLETADO")
            log_queue.put(f"[*] Total: {total_procesados} | Exitosos: {total_exitosos} | Errores: {total_errores}")

    except Exception as e:
        error_msg = str(e).lower()

        # Mensajes descriptivos sin stacktrace
        if "backend" in error_msg or "connection" in error_msg:
            log_queue.put(f"[ERROR] Error crítico: No se pudo conectar al backend")
        elif "chrome" in error_msg or "driver" in error_msg:
            log_queue.put(f"[ERROR] Error crítico: Problema con Chrome/ChromeDriver")
        elif "session" in error_msg:
            log_queue.put(f"[ERROR] Error crítico: Sesión de Chrome perdida")
        else:
            log_queue.put(f"[ERROR] Error crítico del bot - Reinicia el programa")

    finally:
        settings.bot_corriendo = False
        settings.driver_global = None
