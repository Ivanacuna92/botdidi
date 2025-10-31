"""
Gestión de rutas para desarrollo y producción (.exe)

Este módulo detecta si la aplicación se está ejecutando como .exe compilado
o en modo desarrollo, y establece las rutas apropiadas para cada caso.

Cuando se compila con PyInstaller:
- Archivos temporales (código) van a sys._MEIPASS (carpeta temporal)
- Archivos persistentes (perfil Chrome, token) van a AppData del usuario

En desarrollo:
- Todo se maneja en la carpeta del proyecto
"""
import os
import sys


# ============================================================================
# DETECCIÓN DE MODO
# ============================================================================

# PyInstaller establece sys.frozen = True cuando crea el .exe
IS_FROZEN = getattr(sys, 'frozen', False)


# ============================================================================
# RUTAS BASE
# ============================================================================

if IS_FROZEN:
    # MODO .EXE
    # PyInstaller descomprime archivos incluidos en una carpeta temporal
    TEMP_DIR = sys._MEIPASS

    # Datos persistentes DEBEN ir a AppData (no a la carpeta temporal)
    # La carpeta temporal se borra cuando cierras el .exe
    BASE_DIR = os.path.join(os.environ['APPDATA'], 'BotDidi')

    # Crear carpeta si no existe
    os.makedirs(BASE_DIR, exist_ok=True)

    print(f"[DEBUG] Modo .EXE detectado")
    print(f"[DEBUG] Archivos temporales: {TEMP_DIR}")
    print(f"[DEBUG] Archivos persistentes: {BASE_DIR}")
else:
    # MODO DESARROLLO
    # En desarrollo: usar carpeta del proyecto como base
    TEMP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    BASE_DIR = TEMP_DIR

    # No imprimir en desarrollo para no llenar consola
    # print(f"[DEBUG] Modo desarrollo")
    # print(f"[DEBUG] Carpeta base: {BASE_DIR}")


# ============================================================================
# RUTAS ESPECÍFICAS
# ============================================================================

# Perfil de Chrome (debe persistir entre ejecuciones)
CHROME_PROFILE = os.path.join(BASE_DIR, 'DidiProfile')

# Token de licencia (debe persistir)
TOKEN_PATH = os.path.join(BASE_DIR, '.license_token')

# Configuración de base de datos (debe persistir)
DB_CONFIG_PATH = os.path.join(BASE_DIR, 'db_config.json')

# ChromeDriver (si se incluye en el .exe, estará en TEMP_DIR)
# Si no se incluye, será None y Selenium intentará sin él
CHROMEDRIVER_PATH = os.path.join(TEMP_DIR, 'chromedriver.exe') if IS_FROZEN else None


# ============================================================================
# EXPORTACIONES
# ============================================================================

__all__ = [
    'IS_FROZEN',
    'BASE_DIR',
    'TEMP_DIR',
    'CHROME_PROFILE',
    'TOKEN_PATH',
    'DB_CONFIG_PATH',
    'CHROMEDRIVER_PATH'
]


# ============================================================================
# DEPURACIÓN
# ============================================================================

if __name__ == "__main__":
    """Script de prueba para verificar rutas"""
    print("=" * 70)
    print("CONFIGURACIÓN DE RUTAS")
    print("=" * 70)
    print(f"Modo:                 {'EXE' if IS_FROZEN else 'DESARROLLO'}")
    print(f"BASE_DIR:             {BASE_DIR}")
    print(f"TEMP_DIR:             {TEMP_DIR}")
    print(f"CHROME_PROFILE:       {CHROME_PROFILE}")
    print(f"TOKEN_PATH:           {TOKEN_PATH}")
    print(f"DB_CONFIG_PATH:       {DB_CONFIG_PATH}")
    print(f"CHROMEDRIVER_PATH:    {CHROMEDRIVER_PATH}")
    print("=" * 70)

    # Verificar si las rutas existen
    print("\nESTADO DE RUTAS:")
    print(f"BASE_DIR existe:      {os.path.exists(BASE_DIR)}")
    print(f"CHROME_PROFILE existe: {os.path.exists(CHROME_PROFILE)}")
    print(f"TOKEN existe:         {os.path.exists(TOKEN_PATH)}")
    print(f"DB_CONFIG existe:     {os.path.exists(DB_CONFIG_PATH)}")
    if CHROMEDRIVER_PATH:
        print(f"CHROMEDRIVER existe:  {os.path.exists(CHROMEDRIVER_PATH)}")
