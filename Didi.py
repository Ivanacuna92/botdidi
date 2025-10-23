from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import os
import sys
import requests
import signal
import atexit

# Variable global para trackear clientes procesados
clientes_exitosos_global = 0
guardado_realizado = False  # Flag para evitar guardado duplicado

# Configurar UTF-8 para la consola de Windows (para soportar emojis)
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

def guardar_al_salir():
    """Se ejecuta cuando el script termina (normal o con Ctrl+C)"""
    global clientes_exitosos_global, guardado_realizado

    if guardado_realizado:
        return  # Ya se guardó, no hacer nada

    if clientes_exitosos_global > 0:
        print(f"\n[*] Guardando {clientes_exitosos_global} clientes en la base de datos...")
        registrar_en_base_datos(clientes_exitosos_global)
        guardado_realizado = True
        print(f"[OK] {clientes_exitosos_global} clientes guardados exitosamente")

def signal_handler(sig, frame):
    """Maneja Ctrl+C para guardar antes de salir"""
    print('\n\n[!] Interrupción detectada (Ctrl+C)')
    guardar_al_salir()
    print('[*] Script terminado')
    sys.exit(0)

# Registrar handlers
signal.signal(signal.SIGINT, signal_handler)
atexit.register(guardar_al_salir)

def procesar_registro(driver, indice_registro):
    """
    Procesa un registro completo: Detalles -> WhatsApp -> Plantilla -> Enviar -> Codigo -> Confirmar
    """
    try:
        print(f"\n{'='*60}")
        print(f"[*] PROCESANDO REGISTRO #{indice_registro + 1}")
        print(f"{'='*60}")

        # Esperar a que la tabla esté cargada
        time.sleep(1)

        # Obtener todos los botones "Detalles" de la página actual (solo visibles, no is-hidden)
        botones_detalles = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//td[not(contains(@class, 'is-hidden'))]//button[contains(@class, 'el-button') and .//span[text()='Detalles']]"))
        )

        if indice_registro >= len(botones_detalles):
            print(f"[!] No hay mas registros en esta pagina")
            return False

        boton_detalles = botones_detalles[indice_registro]

        # Scroll al botón y click
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", boton_detalles)
        time.sleep(0.5)

        print(f"[OK] Boton 'Detalles' #{indice_registro} encontrado, haciendo click...")

        try:
            boton_detalles.click()
        except:
            driver.execute_script("arguments[0].click();", boton_detalles)

        time.sleep(2)
        print("[OK] Click en 'Detalles' exitoso")

        # PASO 6: Clickear WhatsApp
        print("\n[*] Clickeando boton WhatsApp...")
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
        print("[OK] WhatsApp clickeado")

        # PASO 7: Seleccionar plantilla de comunicación
        print("\n[*] Seleccionando plantilla de comunicacion...")
        dialog = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'el-dialog')]"))
        )
        time.sleep(1)

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
        print("[OK] Plantilla seleccionada")

        # PASO 8: Clickear plantilla y enviar
        print("\n[*] Enviando mensaje de WhatsApp...")
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

        # Buscar botón Enviar
        botones = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//button[@type='button' and contains(@class, 'el-button--primary') and contains(@class, 'el-button--medium')]"))
        )
        boton_enviar = None
        for boton in botones:
            if "Enviar" in boton.text:
                boton_enviar = boton
                break

        if boton_enviar is None:
            raise Exception("No se encontró el botón Enviar")

        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", boton_enviar)
        time.sleep(0.5)
        try:
            boton_enviar.click()
        except:
            driver.execute_script("arguments[0].click();", boton_enviar)
        time.sleep(2)
        print("[OK] Mensaje enviado")

        # PASO 9: Código del pago
        print("\n[*] Seleccionando codigo del pago...")
        time.sleep(2)

        botones = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//button[@type='button' and contains(@class, 'el-button--primary') and contains(@class, 'el-button--mini')]"))
        )
        boton_codigo = None
        for boton in botones:
            if "Código del pago" in boton.text or "Codigo del pago" in boton.text:
                boton_codigo = boton
                break

        if boton_codigo is None:
            raise Exception("No se encontró el botón Código del pago")

        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", boton_codigo)
        time.sleep(0.5)
        try:
            boton_codigo.click()
        except:
            driver.execute_script("arguments[0].click();", boton_codigo)
        time.sleep(2)
        print("[OK] Modal de codigo abierto")

        # PASO 10: Seleccionar radio button y confirmar
        print("\n[*] Confirmando codigo del pago...")
        modal = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'el-dialog')]"))
        )
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

        # Buscar botón Confirmar
        botones_confirmar = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//button[@type='button' and contains(@class, 'el-button--primary') and contains(@class, 'el-button--medium')]"))
        )
        boton_confirmar = None
        for boton in botones_confirmar:
            if "Confirmar" in boton.text:
                boton_confirmar = boton
                break

        if boton_confirmar is None:
            raise Exception("No se encontró el botón Confirmar")

        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", boton_confirmar)
        time.sleep(0.5)
        try:
            boton_confirmar.click()
        except:
            driver.execute_script("arguments[0].click();", boton_confirmar)
        time.sleep(2)
        print("[OK] Codigo confirmado")

        # Cerrar la pestaña "Detalles del lead"
        print("\n[*] Cerrando pestana del lead...")
        try:
            boton_cerrar_tab = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//span[contains(@class, 'tags-view-item') and contains(., 'Detalles del lead')]//span[contains(@class, 'el-icon-close')]"))
            )
            try:
                boton_cerrar_tab.click()
            except:
                driver.execute_script("arguments[0].click();", boton_cerrar_tab)
            time.sleep(1)
            print("[OK] Pestana cerrada")
        except Exception as e:
            print(f"[!] No se pudo cerrar la pestana automaticamente: {e}")
            # Si falla, intentar volver a la tabla manualmente
            link_mis_casos = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//a[@href='/pixiu/#/my_case/my_case_index']//li[@class='el-menu-item']"))
            )
            try:
                link_mis_casos.click()
            except:
                driver.execute_script("arguments[0].click();", link_mis_casos)
            time.sleep(2)

        print(f"\n[OK] REGISTRO #{indice_registro + 1} COMPLETADO")
        return True

    except Exception as e:
        print(f"\n[ERROR] Error procesando registro #{indice_registro}: {e}")
        import traceback
        traceback.print_exc()
        # Intentar volver a la tabla aunque haya error
        try:
            link_mis_casos = driver.find_element(By.XPATH, "//a[@href='/pixiu/#/my_case/my_case_index']//li[@class='el-menu-item']")
            driver.execute_script("arguments[0].click();", link_mis_casos)
            time.sleep(2)
        except:
            pass
        return False


def registrar_en_base_datos(clientes_procesados):
    """
    Registra en la base de datos cuántos clientes fueron procesados exitosamente
    """
    try:
        print(f"\n[*] Registrando {clientes_procesados} clientes en la base de datos...")
        response = requests.post('http://localhost:5000/registrar',
                                json={'clientes': clientes_procesados},
                                timeout=5)

        if response.status_code == 200:
            print(f"[OK] Registro exitoso en la base de datos")
        else:
            print(f"[!] Error al registrar: {response.text}")
    except Exception as e:
        print(f"[!] No se pudo registrar en la base de datos: {e}")
        print(f"[*] (Asegurate de que backend_conteo.py este corriendo)")


def automate_didi_dashboard():
    """
    RPA para navegar dashboard de Didi y enviar notificaciones a TODOS los registros
    """
    # Conectarse a Chrome existente con sesión activa
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        print("[ERROR] No se pudo conectar a Chrome.")
        print("\n[*] INSTRUCCIONES - CONFIGURACION INICIAL:")
        print("=" * 50)
        print("1. Cierra TODAS las ventanas de Chrome que tengas abiertas")
        print("2. Ejecuta el archivo: abrir_chrome_debug.bat")
        print("3. Se abrira Chrome - Navega a Didi y loguéate manualmente")
        print("4. DEJA ESE CHROME ABIERTO (no lo cierres nunca)")
        print("5. Vuelve a ejecutar: python Didi.py")
        print("=" * 50)
        print("\n[*] Solo necesitas hacer esto UNA VEZ.")
        print("   Despues, siempre deja ese Chrome abierto y ejecuta el script.\n")
        raise

    try:
        print("[OK] Conectado a Chrome exitosamente!")
        print("[*] Usando la sesion existente...")
        time.sleep(2)

        # PASO 1: Esperar a que el menú Element UI cargue
        print("\n[*] Paso 1: Esperando carga del menu vertical...")
        try:
            menu_principal = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//ul[@role='menubar' and contains(@class, 'el-menu')]"))
            )
            print("[OK] Menu principal cargado")
        except Exception as e:
            print(f"[ERROR] Error al cargar menu: {e}")
            raise

        # PASO 2: Expandir "Mesa de trabajo para llamada de cobranza"
        print("\n[*] Paso 2: Expandiendo 'Mesa de trabajo para llamada de cobranza'...")
        try:
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
            print("[OK] Submenu 'Mesa de trabajo' expandido")
        except Exception as e:
            print(f"[ERROR] Error al expandir 'Mesa de trabajo': {e}")
            raise

        # PASO 3: Expandir el submenu interno "Mis casos"
        print("\n[*] Paso 3: Expandiendo submenu 'Mis casos'...")
        try:
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
            print("[OK] Submenu 'Mis casos' expandido")
        except Exception as e:
            print(f"[ERROR] Error al expandir submenu 'Mis casos': {e}")
            raise

        # PASO 4: Clickear el link final "Mis casos"
        print("\n[*] Paso 4: Clickeando link final 'Mis casos'...")
        try:
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
            print("[OK] Pagina 'Mis casos' cargada")
        except Exception as e:
            print(f"[ERROR] Error al clickear link 'Mis casos': {e}")
            raise

        print("\n[OK] Navegacion completada exitosamente!")
        print("[OK] Pagina 'Mis casos' abierta")

        # PASO 5: Procesar TODOS los registros de TODAS las páginas
        print("\n" + "="*70)
        print("[*] INICIANDO PROCESAMIENTO MASIVO DE REGISTROS")
        print("="*70)

        global clientes_exitosos_global

        pagina_actual = 1
        total_procesados = 0
        total_exitosos = 0
        total_errores = 0

        while True:
            print(f"\n{'#'*70}")
            print(f"[*] PAGINA {pagina_actual}")
            print(f"{'#'*70}")

            # Esperar a que la tabla cargue
            tabla = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//table[contains(@class, 'el-table')]"))
            )
            time.sleep(1)

            # Contar cuántos registros hay en esta página (solo botones visibles, no is-hidden)
            botones_detalles = driver.find_elements(By.XPATH, "//td[not(contains(@class, 'is-hidden'))]//button[contains(@class, 'el-button') and .//span[text()='Detalles']]")
            num_registros = len(botones_detalles)
            print(f"[OK] {num_registros} registros encontrados en esta pagina")

            if num_registros == 0:
                print("[!] No hay registros en esta pagina")
                break

            # Procesar cada registro de la página actual
            for i in range(num_registros):
                total_procesados += 1
                exito = procesar_registro(driver, i)
                if exito:
                    total_exitosos += 1
                    clientes_exitosos_global += 1  # Actualizar contador global
                    print(f"[*] Total de clientes exitosos acumulados: {clientes_exitosos_global}")
                else:
                    total_errores += 1

            # Verificar si hay siguiente página
            print(f"\n[*] Buscando siguiente pagina...")
            try:
                # Buscar el botón de "siguiente página" (flecha derecha) en el paginador
                # Verificar que no esté deshabilitado
                boton_siguiente = driver.find_element(By.XPATH, "//button[contains(@class, 'btn-next') and not(@disabled)]//i[contains(@class, 'el-icon-arrow-right')]")

                print(f"[OK] Hay mas paginas, navegando a pagina {pagina_actual + 1}...")

                # Hacer click en el botón padre (el button, no el icono)
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
                print("[OK] No hay mas paginas")
                break

        # Resumen final
        print("\n" + "="*70)
        print("[OK] PROCESAMIENTO COMPLETADO")
        print("="*70)
        print(f"[*] ESTADISTICAS:")
        print(f"   - Total de registros procesados: {total_procesados}")
        print(f"   - Exitosos: {total_exitosos}")
        print(f"   - Con errores: {total_errores}")
        print(f"   - Paginas procesadas: {pagina_actual}")
        print("="*70)

        # El guardado se hace automáticamente al salir (atexit)
        print(f"\n[*] Los {total_exitosos} clientes se guardarán al cerrar el script...")

        time.sleep(2)

    except Exception as e:
        print(f"[ERROR] Error general: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\n[OK] Script finalizado (navegador permanece abierto)")

if __name__ == "__main__":
    automate_didi_dashboard()
