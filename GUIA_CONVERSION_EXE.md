# 🚀 GUÍA COMPLETA: Conversión de Bot Didi a .EXE con PyInstaller

**Fecha de creación:** 30 de Octubre, 2025
**Proyecto:** Bot Didi - Sistema de Automatización
**Objetivo:** Convertir aplicación Python a ejecutable standalone (.exe)

---

## 📋 ÍNDICE

1. [Análisis de Ventajas y Desventajas](#ventajas-y-desventajas)
2. [Desafíos Específicos del Proyecto](#desafíos-específicos)
3. [Cambios Necesarios al Código](#cambios-necesarios)
4. [Plan de Acción Completo](#plan-de-acción)
5. [División del Trabajo](#división-del-trabajo)
6. [Tiempo Estimado](#tiempo-estimado)
7. [Comandos y Scripts](#comandos-y-scripts)

---

## ✅ VENTAJAS Y DESVENTAJAS

### ✅ VENTAJAS para Bot Didi

#### 1. **Distribución Simple**
- Un solo archivo `.exe` → Cliente hace doble clic → funciona
- No necesitas explicar: "instala Python 3.11, pip install -r requirements.txt..."
- Cliente ni siquiera sabe que es Python

#### 2. **Protección Básica del Código**
- Tu código .py se convierte en bytecode
- No es seguridad real (se puede descompilar), pero evita que cliente vea:
  - Credenciales de BD en `config/settings.py`
  - Lógica del sistema de licencias
  - Estructura del proyecto
- Para el 95% de clientes (no técnicos), es suficiente

#### 3. **Control de Versión**
- `BotDidi_v1.0.exe` → Cliente tiene versión específica
- Cuando actualizas: `BotDidi_v1.1.exe`
- No hay "mi primo le instaló algo y ahora no funciona"

---

### ❌ DESVENTAJAS / DESAFÍOS para Bot Didi

#### 1. **TAMAÑO DEL EJECUTABLE: ~150-200 MB**

**Por qué tan grande:**
```
- Python runtime: ~30 MB
- Selenium + libs: ~40 MB
- ChromeDriver: ~15 MB
- Tkinter + dependencias: ~20 MB
- cryptography, bcrypt: ~25 MB
- Flask + waitress: ~15 MB
- pymysql + otras: ~10 MB
= Total: ~155 MB (comprimido con UPX: ~100 MB)
```

**Problema:**
- Enviar 150 MB por email es molesto
- Cliente con internet lento tarda en descargar

**Solución:**
- Subir a Google Drive / Dropbox → Cliente descarga
- O crear instalador que descargue componentes

#### 2. **Antivirus - Falsos Positivos**

**Problema real:**
- Windows Defender / Antivirus detectan .exe de PyInstaller como "sospechoso"
- Cliente ve: "⚠️ Virus detectado"
- Cliente borra tu .exe

**Por qué pasa:**
- Malware usa PyInstaller → Antivirus marca TODO PyInstaller
- Especialmente si el .exe:
  - Abre Chrome con debugging
  - Hace peticiones HTTP
  - Guarda archivos en AppData

**Soluciones:**
1. **Firmar digitalmente el .exe** (costo: $150-400 USD/año)
2. **Subir a VirusTotal y reportar falso positivo** (gratuito)
3. **Incluir en docs: "Si antivirus bloquea, agregar excepción"**
4. **Usar Nuitka en vez de PyInstaller** (más complejo)

---

## 🔧 DESAFÍOS ESPECÍFICOS DEL PROYECTO

### 1. **CHROMEDRIVER**

**Estado actual:**
```python
# chrome/manager.py línea 100
driver = webdriver.Chrome(options=chrome_options)
```

**Problema con PyInstaller:**
- Si usaras `ChromeDriverManager().install()`, fallaría en .exe
- Tu código actual es bueno (se conecta a Chrome existente)

**Solución necesaria:**
- Incluir `chromedriver.exe` en el paquete
- Detectar si estamos en .exe y usar ruta correcta

```python
import sys
import os

# Detectar si estamos en .exe
if getattr(sys, 'frozen', False):
    # Estamos en PyInstaller
    base_path = sys._MEIPASS
    chromedriver_path = os.path.join(base_path, 'chromedriver.exe')
else:
    # Estamos en desarrollo
    chromedriver_path = None  # Usa el del PATH

# En la conexión:
if chromedriver_path and os.path.exists(chromedriver_path):
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
else:
    driver = webdriver.Chrome(options=chrome_options)
```

---

### 2. **PERFIL DE CHROME (DidiProfile/)**

**Estado actual:**
```python
# config/settings.py línea 11
CHROME_PROFILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'DidiProfile')
```

**Problema con .exe:**
- La ruta apuntaría a `C:\Users\Usuario\AppData\Local\Temp\_MEI123456\`
- Carpeta temporal que se borra al cerrar
- Cliente perdería sesión de Didi cada vez

**Solución necesaria:**
```python
import os
import sys

if getattr(sys, 'frozen', False):
    # En .exe: usar carpeta en AppData del usuario
    BASE_DIR = os.path.join(os.environ['APPDATA'], 'BotDidi')
else:
    # En desarrollo: carpeta actual
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

os.makedirs(BASE_DIR, exist_ok=True)
CHROME_PROFILE = os.path.join(BASE_DIR, "DidiProfile")
```

---

### 3. **TOKEN DE LICENCIA (.license_token)**

**Problema similar a DidiProfile:**
- El token se guarda/lee en la carpeta del script
- En .exe, eso sería la carpeta temporal

**Solución:**
```python
# backend/license_utils.py
# Usar la misma lógica de BASE_DIR
from config.paths import BASE_DIR, TOKEN_PATH

# En guardar_token_local():
with open(TOKEN_PATH, 'wb') as f:
    f.write(token_encriptado)

# En leer_token_local():
if not os.path.exists(TOKEN_PATH):
    return None
```

---

### 4. **CREDENCIALES DE BASE DE DATOS**

**Riesgo de seguridad:**

Tu `config/settings.py` tiene:
```python
DB_CONFIG = {
    'host': 'datenbanken.aloia.dev',
    'user': 'aloiadidibot',
    'password': 'aloia2025didi!',  # ← ESTO QUEDA EN EL .EXE
    'database': 'DidiMonitoreo'
}
```

**Cualquiera** con un decompilador básico puede extraer:
- Host de BD
- Usuario
- Contraseña

**Soluciones:**

**Opción A - Archivo de configuración externo (RECOMENDADA):**
```python
# config/settings.py
import json
from config.paths import BASE_DIR

config_file = os.path.join(BASE_DIR, 'db_config.json')

if os.path.exists(config_file):
    with open(config_file, 'r') as f:
        DB_CONFIG = json.load(f)
else:
    # Valores por defecto o lanzar error
    raise Exception("Archivo db_config.json no encontrado")
```

**Archivo db_config.json (en AppData):**
```json
{
    "host": "datenbanken.aloia.dev",
    "port": 3306,
    "user": "aloiadidibot",
    "password": "aloia2025didi!",
    "database": "DidiMonitoreo",
    "charset": "utf8mb4"
}
```

**Opción B - Obfuscación (menos segura):**
```python
import base64

# Codificar contraseña
DB_PASS = base64.b64decode(b'YWxvaWEyMDI1ZGlkaSE=').decode()
# No es seguro, solo dificulta un poco
```

---

### 5. **IMPORTS OCULTOS (Hidden Imports)**

PyInstaller a veces no detecta automáticamente estos módulos:

```bash
--hidden-import=pymysql
--hidden-import=cryptography
--hidden-import=flask
--hidden-import=waitress
--hidden-import=selenium
--hidden-import=bcrypt
--hidden-import=jwt
--hidden-import=tkinter
--hidden-import=psutil
--hidden-import=requests
```

---

### 6. **FLASK EN THREAD DAEMON**

Tu código actual:
```python
# Didi_GUI.pyw línea 58
backend_thread = Thread(target=iniciar_backend, daemon=True)
backend_thread.start()
```

**Ajuste necesario en `backend/flask_server.py`:**
```python
import sys

def iniciar_backend():
    from waitress import serve

    # Detectar si estamos en .exe
    if getattr(sys, 'frozen', False):
        flask_app.config['DEBUG'] = False

    serve(
        flask_app,
        host='127.0.0.1',
        port=5000,
        threads=4,
        _quiet=True  # Silenciar logs en .exe
    )
```

---

## 📝 CAMBIOS NECESARIOS AL CÓDIGO

### Archivo 1: `config/paths.py` (NUEVO)

```python
"""
Gestión de rutas para desarrollo y producción (.exe)
"""
import os
import sys

# Detectar si estamos en .exe compilado con PyInstaller
IS_FROZEN = getattr(sys, 'frozen', False)

if IS_FROZEN:
    # PyInstaller crea una carpeta temporal donde descomprime archivos
    TEMP_DIR = sys._MEIPASS

    # Datos persistentes deben ir en AppData del usuario
    BASE_DIR = os.path.join(os.environ['APPDATA'], 'BotDidi')
    os.makedirs(BASE_DIR, exist_ok=True)
else:
    # En desarrollo: usar carpeta del proyecto
    TEMP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    BASE_DIR = TEMP_DIR

# Rutas importantes
CHROME_PROFILE = os.path.join(BASE_DIR, "DidiProfile")
TOKEN_PATH = os.path.join(BASE_DIR, '.license_token')
DB_CONFIG_PATH = os.path.join(BASE_DIR, 'db_config.json')

# ChromeDriver (en carpeta temporal del .exe, o en desarrollo)
CHROMEDRIVER_PATH = os.path.join(TEMP_DIR, 'chromedriver.exe') if IS_FROZEN else None

# Exportar flag
__all__ = [
    'IS_FROZEN',
    'BASE_DIR',
    'TEMP_DIR',
    'CHROME_PROFILE',
    'TOKEN_PATH',
    'DB_CONFIG_PATH',
    'CHROMEDRIVER_PATH'
]
```

---

### Archivo 2: Modificar `config/settings.py`

```python
"""
Configuración global del Bot Didi
"""
import os
import queue
import json

# Importar gestión de rutas
from config.paths import (
    BASE_DIR,
    CHROME_PROFILE,
    DB_CONFIG_PATH,
    IS_FROZEN
)

# ============================================================================
# BASE DE DATOS (cargada desde archivo externo)
# ============================================================================

# Intentar cargar desde archivo de configuración
if os.path.exists(DB_CONFIG_PATH):
    with open(DB_CONFIG_PATH, 'r', encoding='utf-8') as f:
        DB_CONFIG = json.load(f)
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

    # Si estamos en .exe y no existe el archivo, crearlo
    if IS_FROZEN:
        os.makedirs(os.path.dirname(DB_CONFIG_PATH), exist_ok=True)
        with open(DB_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(DB_CONFIG, f, indent=4)

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
```

---

### Archivo 3: Modificar `backend/license_utils.py`

```python
# Cambiar esta línea (aproximadamente línea 15):
# DE:
# TOKEN_FILE = '.license_token'

# A:
from config.paths import TOKEN_PATH

# Y en todas las funciones, reemplazar '.license_token' por TOKEN_PATH

# Ejemplo en guardar_token_local():
def guardar_token_local(clave, hardware_id):
    """Guarda token local encriptado"""
    from config.paths import TOKEN_PATH  # Importar aquí si no está al inicio

    # ... resto del código ...

    with open(TOKEN_PATH, 'wb') as f:
        f.write(token_encriptado)

# Ejemplo en leer_token_local():
def leer_token_local():
    """Lee y valida token local"""
    from config.paths import TOKEN_PATH

    if not os.path.exists(TOKEN_PATH):
        return None

    # ... resto del código ...
```

---

### Archivo 4: Modificar `chrome/manager.py` (opcional, solo si es necesario)

```python
# Línea 100 aproximadamente
# Agregar soporte para chromedriver.exe incluido

from config.paths import CHROMEDRIVER_PATH, IS_FROZEN
from selenium.webdriver.chrome.service import Service

def conectar_a_chrome():
    """Se conecta a Chrome con reintentos"""
    log_queue.put("[*] Conectando al navegador...")

    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{CHROME_DEBUG_PORT}")

    driver = None
    for intento in range(3):
        try:
            # Si estamos en .exe y existe chromedriver incluido
            if IS_FROZEN and CHROMEDRIVER_PATH and os.path.exists(CHROMEDRIVER_PATH):
                service = Service(CHROMEDRIVER_PATH)
                driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                driver = webdriver.Chrome(options=chrome_options)

            log_queue.put("[OK] Conectado a Chrome exitosamente")

            # ... resto del código sin cambios ...
```

---

### Archivo 5: Modificar `backend/flask_server.py`

```python
# Agregar al inicio del archivo
import sys
from config.paths import IS_FROZEN

def iniciar_backend():
    """Inicia el servidor backend Flask con Waitress"""
    from waitress import serve

    # Deshabilitar debug mode en .exe
    if IS_FROZEN:
        flask_app.config['DEBUG'] = False
        flask_app.config['PROPAGATE_EXCEPTIONS'] = False

    print(f"[*] Backend Flask iniciando en http://{BACKEND_HOST}:{BACKEND_PORT}")

    serve(
        flask_app,
        host=BACKEND_HOST,
        port=BACKEND_PORT,
        threads=BACKEND_THREADS,
        _quiet=IS_FROZEN  # Silenciar logs solo en .exe
    )
```

---

## 🎯 PLAN DE ACCIÓN COMPLETO

### FASE 1: Preparación del Código (YO - Claude)

**Tiempo estimado: 1-2 horas**

- [x] Crear `config/paths.py`
- [x] Modificar `config/settings.py`
- [x] Modificar `backend/license_utils.py`
- [x] Modificar `backend/flask_server.py`
- [x] (Opcional) Modificar `chrome/manager.py`
- [x] Crear `BotDidi.spec` (configuración PyInstaller)
- [x] Crear `compilar.bat` (script de compilación)
- [x] Crear `db_config.json.example`
- [x] Crear `README_CLIENTE.txt`
- [x] Crear `INSTRUCCIONES_COMPILACION.md`

---

### FASE 2: Descargar Dependencias (TÚ)

**Tiempo estimado: 5-10 minutos**

1. **Descargar ChromeDriver:**
   - Ir a: https://googlechromelabs.github.io/chrome-for-testing/
   - Verificar tu versión de Chrome: `chrome://version`
   - Descargar ChromeDriver que coincida
   - Guardar `chromedriver.exe` en la raíz del proyecto

2. **Instalar PyInstaller (si no lo tienes):**
   ```bash
   pip install pyinstaller
   ```

---

### FASE 3: Compilación (TÚ)

**Tiempo estimado: 5 minutos**

```bash
# Opción 1: Usando el script
doble clic en: compilar.bat

# Opción 2: Manual
pyinstaller BotDidi.spec
```

**Resultado esperado:**
```
build/                  (archivos temporales)
dist/
  └── BotDidi.exe      (¡TU EJECUTABLE!)
```

---

### FASE 4: Pruebas Locales (TÚ)

**Tiempo estimado: 30 minutos**

1. **Primera ejecución:**
   ```bash
   cd dist
   BotDidi.exe
   ```

2. **Verificar que funcione:**
   - ✅ Backend inicia correctamente
   - ✅ Pantalla de activación aparece (si no hay token)
   - ✅ Licencia se valida
   - ✅ Login funciona
   - ✅ Chrome se conecta
   - ✅ Bot procesa clientes

3. **Verificar archivos persistentes:**
   ```
   C:\Users\TuUsuario\AppData\Roaming\BotDidi\
     ├── DidiProfile\
     ├── .license_token
     └── db_config.json
   ```

---

### FASE 5: Prueba en Máquina Limpia (TÚ - Opcional)

**Tiempo estimado: 1 hora**

1. **Copiar a otra PC:**
   - PC sin Python instalado
   - Copiar solo `BotDidi.exe`

2. **Primera ejecución en PC limpia:**
   - Ejecutar `BotDidi.exe`
   - Debería pedir activación de licencia
   - Activar con una clave válida
   - Probar flujo completo

3. **Si hay errores:**
   - Capturar el mensaje de error completo
   - Mandármelo
   - Yo lo soluciono (probablemente falta un hidden-import)

---

### FASE 6: Resolución de Problemas (YO/TÚ)

**Errores comunes y soluciones:**

#### Error: "No module named 'xyz'"
**Solución:** Agregar hidden-import
```python
# En BotDidi.spec, agregar:
hiddenimports=['xyz']
```

#### Error: "chromedriver not found"
**Solución:** Verificar que se incluyó en datas
```python
# En BotDidi.spec:
datas=[('chromedriver.exe', '.')],
```

#### Error: "Backend no disponible"
**Solución:** Verificar puerto 5000 libre, firewall

#### Error: Antivirus lo bloquea
**Solución:** Agregar excepción temporal o firmar el .exe

---

## 📊 DIVISIÓN DEL TRABAJO

| Tarea | Responsable | Tiempo | % |
|-------|-------------|--------|---|
| Crear config/paths.py | Claude | 15 min | 5% |
| Modificar settings.py | Claude | 20 min | 7% |
| Modificar license_utils.py | Claude | 15 min | 5% |
| Modificar flask_server.py | Claude | 10 min | 3% |
| Modificar chrome/manager.py | Claude | 15 min | 5% |
| Crear BotDidi.spec | Claude | 20 min | 7% |
| Crear scripts y docs | Claude | 30 min | 10% |
| **Subtotal Claude** | **Claude** | **~2 horas** | **42%** |
| Descargar ChromeDriver | Tú | 5 min | 2% |
| Ejecutar compilación | Tú | 5 min | 2% |
| Probar .exe localmente | Tú | 30 min | 10% |
| Probar en PC limpia | Tú | 1 hora | 25% |
| Resolver errores (iteración) | Tú + Claude | Variable | 19% |
| **Subtotal Tú** | **Tú** | **~2 horas** | **58%** |
| **TOTAL** | - | **~4 horas** | **100%** |

---

## ⏱️ TIEMPO ESTIMADO TOTAL

### Escenario Optimista (todo sale bien):
```
Claude: 2 horas
Tú:    40 minutos (sin prueba en PC limpia)
TOTAL: ~3 horas
```

### Escenario Realista (1-2 errores):
```
Claude: 2 horas
Tú:    2 horas (con pruebas y 1-2 iteraciones)
TOTAL: ~4 horas
```

### Escenario Pesimista (muchos errores):
```
Claude: 3 horas
Tú:    4 horas (múltiples iteraciones)
TOTAL: ~7 horas
```

---

## 📦 TAMAÑO FINAL ESTIMADO

```
BotDidi.exe: ~180 MB (sin UPX)
BotDidi.exe: ~120 MB (con UPX compression - opcional)

Primera ejecución crea:
C:\Users\Cliente\AppData\Roaming\BotDidi\
  ├── DidiProfile\        (~50 MB después de usar Chrome)
  ├── .license_token      (500 bytes)
  └── db_config.json      (200 bytes)

Total en disco: ~170-230 MB
```

---

## 🛠️ COMANDOS Y SCRIPTS

### Comando de Compilación Completo

```bash
pyinstaller --onefile ^
    --windowed ^
    --name="BotDidi" ^
    --icon="icono.ico" ^
    --add-data="chromedriver.exe;." ^
    --hidden-import=pymysql ^
    --hidden-import=cryptography ^
    --hidden-import=flask ^
    --hidden-import=waitress ^
    --hidden-import=selenium ^
    --hidden-import=bcrypt ^
    --hidden-import=jwt ^
    --hidden-import=psutil ^
    --hidden-import=requests ^
    --hidden-import=tkinter ^
    --hidden-import=queue ^
    --hidden-import=threading ^
    --noupx ^
    --clean ^
    Didi_GUI.pyw
```

**Explicación de parámetros:**
- `--onefile`: Todo en un solo .exe
- `--windowed`: Sin consola (solo GUI)
- `--name`: Nombre del ejecutable
- `--icon`: Ícono del .exe (opcional)
- `--add-data`: Incluir chromedriver.exe
- `--hidden-import`: Módulos que PyInstaller no detecta automáticamente
- `--noupx`: No comprimir (evita falsos positivos de antivirus)
- `--clean`: Limpiar archivos temporales antes de compilar

---

### Script: `compilar.bat`

```batch
@echo off
echo ============================================
echo   COMPILANDO BOT DIDI A EJECUTABLE
echo ============================================
echo.

REM Verificar que existe chromedriver.exe
if not exist "chromedriver.exe" (
    echo [ERROR] No se encontro chromedriver.exe
    echo Por favor descarga ChromeDriver y colocalo en esta carpeta
    echo URL: https://googlechromelabs.github.io/chrome-for-testing/
    pause
    exit /b 1
)

echo [1/3] Limpiando compilaciones anteriores...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "BotDidi.spec" del BotDidi.spec

echo [2/3] Compilando con PyInstaller...
echo (Esto puede tomar 3-5 minutos)
echo.

pyinstaller --onefile ^
    --windowed ^
    --name="BotDidi" ^
    --add-data="chromedriver.exe;." ^
    --hidden-import=pymysql ^
    --hidden-import=cryptography ^
    --hidden-import=flask ^
    --hidden-import=waitress ^
    --hidden-import=selenium ^
    --hidden-import=bcrypt ^
    --hidden-import=jwt ^
    --hidden-import=psutil ^
    --hidden-import=requests ^
    --hidden-import=tkinter ^
    --noupx ^
    --clean ^
    Didi_GUI.pyw

if errorlevel 1 (
    echo.
    echo [ERROR] La compilacion fallo
    pause
    exit /b 1
)

echo.
echo [3/3] Compilacion exitosa!
echo.
echo Archivo generado: dist\BotDidi.exe
echo.

REM Verificar tamaño
for %%I in (dist\BotDidi.exe) do echo Tamano: %%~zI bytes (~%%~zI / 1048576 MB)

echo.
echo ============================================
echo   COMPILACION COMPLETA
echo ============================================
echo.
echo Siguiente paso: Probar dist\BotDidi.exe
echo.

pause
```

---

### Archivo: `db_config.json.example`

```json
{
    "host": "datenbanken.aloia.dev",
    "port": 3306,
    "user": "aloiadidibot",
    "password": "aloia2025didi!",
    "database": "DidiMonitoreo",
    "charset": "utf8mb4"
}
```

**Instrucción:**
```
1. Copiar este archivo a: C:\Users\TuUsuario\AppData\Roaming\BotDidi\
2. Renombrar a: db_config.json
3. Editar credenciales si es necesario
```

---

### Archivo: `README_CLIENTE.txt`

```
================================================================================
                        BOT DIDI - GUÍA DE INSTALACIÓN
================================================================================

REQUISITOS PREVIOS:
-------------------
✓ Windows 10/11
✓ Google Chrome instalado
✓ Conexión a Internet
✓ Clave de licencia válida (formato: DIDI-XXXX-XXXX-XXXX)


INSTALACIÓN:
-----------
1. Descargar BotDidi.exe
2. Colocar en una carpeta (ej: C:\BotDidi\)
3. Ejecutar BotDidi.exe


PRIMERA EJECUCIÓN:
------------------
1. Se abrirá ventana de "Activación de Licencia"
2. Ingresar su clave de licencia
3. Hacer clic en "ACTIVAR LICENCIA"
4. Si la activación es exitosa, continuar al login
5. Ingresar usuario y contraseña proporcionados


USO NORMAL:
-----------
1. Ejecutar BotDidi.exe
2. El sistema validará su licencia automáticamente
3. Ingresar credenciales de login
4. Usar el bot normalmente


ARCHIVOS GENERADOS:
-------------------
El bot crea archivos en:
C:\Users\SuUsuario\AppData\Roaming\BotDidi\

- DidiProfile\      → Perfil de Chrome (sesión de Didi)
- .license_token    → Token de licencia
- db_config.json    → Configuración de base de datos


SOLUCIÓN DE PROBLEMAS:
----------------------

1. "Error al validar licencia"
   → Verificar conexión a Internet
   → Verificar que la clave sea correcta

2. "Backend no disponible"
   → Cerrar el programa completamente
   → Reiniciar BotDidi.exe
   → Si persiste, verificar que puerto 5000 esté libre

3. "Chrome no se conecta"
   → Cerrar todas las ventanas de Chrome manualmente
   → Reiniciar BotDidi.exe

4. Antivirus bloquea el programa
   → Agregar excepción para BotDidi.exe
   → El programa NO es un virus (falso positivo común con ejecutables Python)


SOPORTE:
--------
Contactar al administrador del sistema con:
- Descripción del problema
- Captura de pantalla del error
- Archivo de log (si aplica)


================================================================================
```

---

## 🚀 PRÓXIMOS PASOS (MAÑANA)

### Checklist de Inicio:

- [ ] Revisar esta guía completa
- [ ] Confirmar que quieres proceder con PyInstaller
- [ ] Yo (Claude) creo todos los archivos necesarios
- [ ] Tú descargas ChromeDriver
- [ ] Yo reviso que todos los cambios sean correctos
- [ ] Tú ejecutas compilación
- [ ] Probamos y resolvemos errores juntos

---

## 📝 NOTAS FINALES

### Recordatorios Importantes:

1. **Backup:** Hacer commit de git antes de empezar
2. **ChromeDriver:** Debe coincidir con versión de Chrome instalada
3. **Antivirus:** Desactivar temporalmente durante compilación
4. **Paciencia:** Primera compilación puede tomar 5-10 minutos
5. **Iteración:** Es normal tener 1-2 errores en primera compilación

### Alternativas Consideradas:

Si PyInstaller da muchos problemas, podemos intentar:
1. **Nuitka** - Compila a C++ nativo (más lento de compilar, mejor resultado)
2. **cx_Freeze** - Alternativa a PyInstaller
3. **Instalador MSI** - Más profesional, requiere más trabajo
4. **Python Portable** - Distribuir Python + scripts empaquetados

---

**¡Nos vemos mañana para implementar esto! 🚀**
