"""
Verificación de sesión de Didi
"""
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config.settings import DIDI_DASHBOARD_URLS, tipo_recorrido_actual, log_queue
import config.settings as settings


def verificar_sesion_didi(driver):
    """Verifica si el usuario está logueado y en la URL correcta"""
    try:
        # Obtener URL según el tipo de recorrido seleccionado
        url_esperada = DIDI_DASHBOARD_URLS.get(settings.tipo_recorrido_actual, DIDI_DASHBOARD_URLS['CreditCard'])
        log_queue.put(f"[*] Tipo de recorrido: {settings.tipo_recorrido_actual}")

        # Intentar obtener URL actual
        url_actual = None
        try:
            url_actual = driver.current_url
            log_queue.put(f"[DEBUG] URL actual: {url_actual}")
        except Exception as e:
            error_msg = str(e).lower()

            # Si es error de contexto, intentar recuperar
            if "execution context" in error_msg or "no such window" in error_msg or "frame" in error_msg:
                log_queue.put("[!] Contexto de pestana perdido, intentando recuperar...")

                # ESTRATEGIA 1: Intentar cambiar a todas las pestanas hasta encontrar una valida
                try:
                    log_queue.put("[*] Buscando pestana valida...")
                    handles = driver.window_handles
                    log_queue.put(f"[DEBUG] Encontradas {len(handles)} pestanas")

                    for i, handle in enumerate(handles):
                        try:
                            driver.switch_to.window(handle)
                            test_url = driver.current_url  # Test si esta pestana funciona
                            log_queue.put(f"[OK] Pestana {i+1} es valida, usando esta")
                            url_actual = test_url
                            break
                        except:
                            log_queue.put(f"[!] Pestana {i+1} invalida, probando siguiente...")
                            continue
                except Exception as e2:
                    log_queue.put(f"[!] No se pudo cambiar de pestana: {str(e2)}")

                # ESTRATEGIA 2: Si ninguna pestana funciona, navegar directamente
                if url_actual is None:
                    log_queue.put("[*] Todas las pestanas invalidas, navegando directamente...")
                    try:
                        driver.set_page_load_timeout(30)  # Aumentar timeout
                        driver.get(url_esperada)
                        time.sleep(5)
                        url_actual = driver.current_url
                        log_queue.put(f"[OK] Navegacion directa exitosa: {url_actual}")
                    except Exception as e3:
                        log_queue.put(f"[ERROR] No se pudo recuperar contexto: {str(e3)[:200]}")
                        # Última oportunidad: crear nueva pestaña
                        log_queue.put("[*] Intentando crear nueva pestana como ultimo recurso...")
                        try:
                            driver.execute_script("window.open('about:blank', '_blank');")
                            time.sleep(2)
                            driver.switch_to.window(driver.window_handles[-1])
                            driver.get(url_esperada)
                            time.sleep(5)
                            url_actual = driver.current_url
                            log_queue.put(f"[OK] Nueva pestana creada exitosamente: {url_actual}")
                        except Exception as e4:
                            log_queue.put(f"[ERROR] Fallo total al crear nueva pestana: {str(e4)[:200]}")
                            return False
            else:
                # Otro tipo de error, intentar navegar directamente
                log_queue.put("[!] Error obteniendo URL, navegando al dashboard...")
                try:
                    driver.get(url_esperada)
                    time.sleep(5)
                    url_actual = driver.current_url
                    log_queue.put(f"[DEBUG] URL despues de navegar: {url_actual}")
                except:
                    return False

        # Si todavia no tenemos URL, fallar
        if url_actual is None:
            log_queue.put("[ERROR] No se pudo obtener URL valida")
            return False

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
