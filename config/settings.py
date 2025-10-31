"""
Configuración global del Bot Didi
"""
import os
import queue
import json

# ============================================================================
# RUTAS DINÁMICAS (desarrollo vs .exe)
# ============================================================================

# Importar gestión de rutas que detecta automáticamente el modo
from config.paths import (
    BASE_DIR,
    CHROME_PROFILE,
    DB_CONFIG_PATH,
    IS_FROZEN
)

# ============================================================================
# BASE DE DATOS
# ============================================================================

# Intentar cargar configuración desde archivo externo
# Esto protege las credenciales cuando distribuimos el .exe
if os.path.exists(DB_CONFIG_PATH):
    # Si existe el archivo, cargar desde ahí
    try:
        with open(DB_CONFIG_PATH, 'r', encoding='utf-8') as f:
            DB_CONFIG = json.load(f)
        if IS_FROZEN:
            print(f"[OK] Configuración de BD cargada desde: {DB_CONFIG_PATH}")
    except Exception as e:
        print(f"[ERROR] No se pudo cargar db_config.json: {e}")
        # Usar valores por defecto como fallback
        DB_CONFIG = {
            'host': 'datenbanken.aloia.dev',
            'port': 3306,
            'user': 'aloiadidibot',
            'password': 'aloia2025didi!',
            'database': 'DidiMonitoreo',
            'charset': 'utf8mb4'
        }
else:
    # Valores por defecto (desarrollo)
    DB_CONFIG = {
        'host': 'datenbanken.aloia.dev',
        'port': 3306,
        'user': 'aloiadidibot',
        'password': 'aloia2025didi!',
        'database': 'DidiMonitoreo',
        'charset': 'utf8mb4'
    }

    # Si estamos en .exe y no existe el archivo, crearlo automáticamente
    if IS_FROZEN:
        try:
            os.makedirs(os.path.dirname(DB_CONFIG_PATH), exist_ok=True)
            with open(DB_CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(DB_CONFIG, f, indent=4)
            print(f"[*] Archivo db_config.json creado en: {DB_CONFIG_PATH}")
        except Exception as e:
            print(f"[!] No se pudo crear db_config.json: {e}")

# ============================================================================
# URLS
# ============================================================================

DIDI_LOGIN_URL = "https://me.didiglobal.com/project/stargate-auth/html/login.html?redirect_uri=https%3A%2F%2Fmis-auth.didiglobal.com%2Fauth%3Fjumpto%3D%2F%26app_id%3D2054"
DIDI_DASHBOARD_URL = "https://pixiu-prod.didiglobal.com/global-fintech/creditcard/mx/global-pixiu-api/home#/index"

# ============================================================================
# CONFIGURACIÓN DE CHROME
# ============================================================================

CHROME_DEBUG_PORT = 9222

CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
]

# ============================================================================
# CONFIGURACIÓN DEL BACKEND
# ============================================================================

BACKEND_HOST = '127.0.0.1'
BACKEND_PORT = 5000
BACKEND_THREADS = 4

# ============================================================================
# VARIABLES GLOBALES DE ESTADO
# ============================================================================

# Variables globales para el bot
clientes_exitosos_global = 0
bot_corriendo = False
detener_bot = False
flask_app = None
driver_global = None

# Colas para comunicación entre threads y GUI
log_queue = queue.Queue()
stats_queue = queue.Queue()
