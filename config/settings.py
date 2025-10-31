"""
Configuración global del Bot Didi
"""
import os
import queue

# ============================================================================
# RUTAS Y PERFILES
# ============================================================================

CHROME_PROFILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'DidiProfile')

# ============================================================================
# BASE DE DATOS
# ============================================================================

DB_CONFIG = {
    'host': 'datenbanken.aloia.dev',
    'port': 3306,
    'user': 'aloiadidibot',
    'password': 'aloia2025didi!',
    'database': 'DidiMonitoreo',
    'charset': 'utf8mb4'
}

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
