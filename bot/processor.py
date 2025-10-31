"""
Procesamiento de registros individuales
"""
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import config.settings as settings
from config.settings import log_queue


def cerrar_pestanas_detalles_abiertas(driver):
    """Cierra cualquier pestana de 'Detalles del lead' que pueda estar abierta"""
    try:
        # Intentar cerrar pestaña de detalles usando el botón X
        try:
            boton_cerrar_tab = driver.find_element(By.XPATH, "//span[contains(@class, 'tags-view-item') and contains(., 'Detalles del lead')]//span[contains(@class, 'el-icon-close')]")
            try:
                boton_cerrar_tab.click()
            except:
                driver.execute_script("arguments[0].click();", boton_cerrar_tab)
            log_queue.put("[OK] Pestaña de 'Detalles del lead' previa cerrada correctamente")
            time.sleep(1)
            return True
        except:
            # No hay pestaña de detalles abierta, todo bien
            return False
    except Exception as e:
        # Si hay un error, intentar navegar a Mis casos como fallback
        try:
            link_mis_casos = driver.find_element(By.XPATH, "//a[@href='/pixiu/#/my_case/my_case_index']//li[@class='el-menu-item']")
            driver.execute_script("arguments[0].click();", link_mis_casos)
            log_queue.put("[OK] Navegado a 'Mis casos' para limpiar vista")
            time.sleep(2)
            return True
        except:
            pass
        return False


def procesar_registro(driver, indice_registro):
    """Procesa un registro completo"""
    if settings.detener_bot:
        datos_cliente = {
            'nombre': 'DETENIDO',
            'cfrnid': 'N/A',
            'monto_total': '0.00'
        }
        return False, datos_cliente

    try:
        # Asegurarse de que no haya pestañas de detalles previas abiertas
        cerrar_pestanas_detalles_abiertas(driver)

        log_queue.put(f"[*] Procesando registro #{indice_registro + 1}")

        time.sleep(1)

        botones_detalles = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//td[not(contains(@class, 'is-hidden'))]//button[contains(@class, 'el-button') and .//span[text()='Detalles']]"))
        )

        if indice_registro >= len(botones_detalles):
            datos_cliente = {
                'nombre': 'SIN_REGISTROS',
                'cfrnid': 'N/A',
                'monto_total': '0.00'
            }
            return False, datos_cliente

        boton_detalles = botones_detalles[indice_registro]

        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", boton_detalles)
        time.sleep(0.5)

        try:
            boton_detalles.click()
        except:
            driver.execute_script("arguments[0].click();", boton_detalles)

        # Esperar a que la vista de detalles abra
        time.sleep(3)

        # Verificar si se debe detener
        if settings.detener_bot:
            log_queue.put("[!] Bot detenido por el usuario")
            datos_cliente = {
                'nombre': 'DETENIDO',
                'cfrnid': 'N/A',
                'monto_total': '0.00'
            }
            return False, datos_cliente

        # Capturar el nombre del cliente desde la vista de detalles
        nombre_cliente = "DESCONOCIDO"
        cfrnid = "DESCONOCIDO"
        monto_total = "0.00"

        try:
            log_queue.put("[*] Capturando datos del cliente desde vista de detalles...")

            # VERIFICAR que la vista de detalles realmente se abrió
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'el-descriptions')]"))
                )
                log_queue.put("[OK] Vista de detalles cargada correctamente")
            except:
                log_queue.put("[ERROR] La vista de detalles NO se abrió")

                # DIAGNÓSTICO: Investigar qué pasó
                try:
                    url_actual = driver.current_url
                    log_queue.put(f"[DEBUG] URL actual: {url_actual}")
                except:
                    log_queue.put("[DEBUG] No se pudo obtener URL")

                # Verificar si hay iframes
                try:
                    iframes = driver.find_elements(By.TAG_NAME, "iframe")
                    if len(iframes) > 0:
                        log_queue.put(f"[DEBUG] ⚠️ Se detectaron {len(iframes)} iframes - posible causa del problema")
                    else:
                        log_queue.put("[DEBUG] No hay iframes detectados")
                except:
                    pass

                # Verificar qué clase de divs SÍ existen
                try:
                    divs = driver.find_elements(By.TAG_NAME, "div")
                    log_queue.put(f"[DEBUG] Se encontraron {len(divs)} divs en la página")

                    # Buscar divs con clases relacionadas a "details" o "detalles"
                    divs_relevantes = driver.find_elements(By.XPATH, "//div[contains(@class, 'detail') or contains(@class, 'drawer') or contains(@class, 'modal')]")
                    if len(divs_relevantes) > 0:
                        log_queue.put(f"[DEBUG] Se encontraron {len(divs_relevantes)} divs con clases relacionadas")
                except:
                    pass

                # Si la vista no se abrió, no vale la pena intentar capturar datos
                raise Exception("Vista de detalles no disponible")

            # Esperar extra para que todos los campos carguen completamente
            time.sleep(1.5)

            # Capturar Nombre
            try:
                elemento_nombre = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//span[@class='el-descriptions-item__label has-colon ' and contains(text(), 'Nombre')]/following-sibling::span[@class='el-descriptions-item__content']"))
                )
                nombre_cliente = elemento_nombre.text.strip()
                log_queue.put(f"[OK] ✓ Cliente capturado: {nombre_cliente}")
            except Exception as e:
                error_msg = str(e).lower()
                if "timeout" in error_msg or "time out" in error_msg:
                    log_queue.put(f"[!] No se pudo capturar nombre: Página no cargó a tiempo")

                    # DIAGNÓSTICO: Ver qué labels SÍ existen
                    try:
                        labels = driver.find_elements(By.XPATH, "//span[@class='el-descriptions-item__label has-colon ']")
                        if len(labels) > 0:
                            textos_labels = [label.text.strip() for label in labels[:5]]  # Primeros 5
                            log_queue.put(f"[DEBUG] Labels encontrados: {', '.join(textos_labels)}")
                        else:
                            log_queue.put("[DEBUG] No se encontraron labels con la clase esperada")

                            # Buscar con XPath más genérico
                            all_spans = driver.find_elements(By.TAG_NAME, "span")
                            log_queue.put(f"[DEBUG] Total de spans en página: {len(all_spans)}")
                    except:
                        pass

                elif "no such element" in error_msg:
                    log_queue.put(f"[!] No se pudo capturar nombre: Campo no encontrado en la página")
                else:
                    log_queue.put(f"[!] No se pudo capturar nombre del cliente")

            # Capturar cfrnid
            try:
                elemento_cfrnid = driver.find_element(By.XPATH, "//span[@class='el-descriptions-item__label has-colon ' and contains(text(), 'cfrnid')]/following-sibling::span[@class='el-descriptions-item__content']")
                cfrnid = elemento_cfrnid.text.strip()
                log_queue.put(f"[OK] ✓ cfrnid capturado: {cfrnid}")
            except Exception as e:
                error_msg = str(e).lower()
                if "no such element" in error_msg:
                    log_queue.put(f"[!] No se pudo capturar cfrnid: Campo no existe en este registro")
                else:
                    log_queue.put(f"[!] No se pudo capturar cfrnid")

            # Capturar Monto total del estado de cuenta (ignorando el icono)
            try:
                elemento_monto = driver.find_element(By.XPATH, "//span[@class='el-descriptions-item__label has-colon ' and contains(text(), 'Monto total del estado de cuenta')]/following-sibling::span[@class='el-descriptions-item__content']")
                monto_total = elemento_monto.text.strip()
                log_queue.put(f"[OK] ✓ Monto total capturado: {monto_total}")
            except Exception as e:
                error_msg = str(e).lower()
                if "no such element" in error_msg:
                    log_queue.put(f"[!] No se pudo capturar monto: Campo no existe en este registro")
                else:
                    log_queue.put(f"[!] No se pudo capturar monto total")

        except Exception as e:
            log_queue.put(f"[ERROR] Error general capturando datos: {str(e)}")
            nombre_cliente = "DESCONOCIDO"

        # Verificar si se debe detener
        if settings.detener_bot:
            log_queue.put("[!] Bot detenido por el usuario")
            return False, nombre_cliente

        log_queue.put(f"[*] Continuando con cliente: {nombre_cliente}")

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
        if settings.detener_bot:
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
        if settings.detener_bot:
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
        if settings.detener_bot:
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

        # Retornar diccionario con todos los datos capturados
        datos_cliente = {
            'nombre': nombre_cliente,
            'cfrnid': cfrnid,
            'monto_total': monto_total
        }
        return True, datos_cliente

    except Exception as e:
        nombre_cliente = locals().get('nombre_cliente', 'DESCONOCIDO')
        cfrnid = locals().get('cfrnid', 'DESCONOCIDO')
        monto_total = locals().get('monto_total', '0.00')

        # Determinar en qué paso falló para dar mensaje más específico
        error_msg = str(e).lower()

        if "no such window" in error_msg or "invalid session" in error_msg:
            log_queue.put(f"[ERROR] Registro #{indice_registro + 1}: Chrome perdió la conexión - {nombre_cliente}")
        elif "timeout" in error_msg or "time out" in error_msg:
            log_queue.put(f"[ERROR] Registro #{indice_registro + 1}: Timeout esperando elemento - {nombre_cliente}")
        elif "no such element" in error_msg or "unable to locate" in error_msg:
            log_queue.put(f"[ERROR] Registro #{indice_registro + 1}: No se encontró elemento en la página - {nombre_cliente}")
        elif "stale element" in error_msg:
            log_queue.put(f"[ERROR] Registro #{indice_registro + 1}: Elemento desactualizado (página cambió) - {nombre_cliente}")
        elif "execution context" in error_msg or "frame" in error_msg:
            log_queue.put(f"[ERROR] Registro #{indice_registro + 1}: Contexto de página perdido - {nombre_cliente}")
        else:
            # Para otros errores, mostrar mensaje genérico sin stacktrace
            log_queue.put(f"[ERROR] Registro #{indice_registro + 1}: Error procesando cliente - {nombre_cliente}")

        try:
            link_mis_casos = driver.find_element(By.XPATH, "//a[@href='/pixiu/#/my_case/my_case_index']//li[@class='el-menu-item']")
            driver.execute_script("arguments[0].click();", link_mis_casos)
            time.sleep(2)
        except:
            pass

        # Retornar diccionario incluso en caso de error
        datos_cliente = {
            'nombre': nombre_cliente,
            'cfrnid': cfrnid,
            'monto_total': monto_total
        }
        return False, datos_cliente
