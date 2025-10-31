"""
Navegación dentro de la plataforma Didi
"""
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config.settings import log_queue


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
