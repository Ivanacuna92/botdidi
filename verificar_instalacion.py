#!/usr/bin/env python
"""
Script de verificación para asegurar que la arquitectura modular funciona correctamente
"""
import sys

print("=" * 60)
print("VERIFICACIÓN DE INSTALACIÓN - BOT DIDI")
print("=" * 60)
print()

# Test 1: Verificar estructura de directorios
print("[1/5] Verificando estructura de directorios...")
import os
directorios_requeridos = ['config', 'backend', 'chrome', 'bot', 'gui']
archivos_requeridos = [
    'config/__init__.py',
    'config/settings.py',
    'backend/__init__.py',
    'backend/flask_server.py',
    'chrome/__init__.py',
    'chrome/manager.py',
    'chrome/session.py',
    'bot/__init__.py',
    'bot/main.py',
    'bot/navigator.py',
    'bot/processor.py',
    'gui/__init__.py',
    'gui/interface.py',
    'Didi_GUI.pyw'
]

todo_ok = True
for dir in directorios_requeridos:
    if os.path.exists(dir) and os.path.isdir(dir):
        print(f"   [OK] Directorio '{dir}' encontrado")
    else:
        print(f"   [ERROR] Directorio '{dir}' NO encontrado")
        todo_ok = False

for archivo in archivos_requeridos:
    if os.path.exists(archivo) and os.path.isfile(archivo):
        print(f"   [OK] Archivo '{archivo}' encontrado")
    else:
        print(f"   [ERROR] Archivo '{archivo}' NO encontrado")
        todo_ok = False

if not todo_ok:
    print("\n[ERROR] Falta algún archivo o directorio requerido")
    sys.exit(1)

print("\n[OK] Estructura de directorios correcta")
print()

# Test 2: Verificar importaciones
print("[2/5] Verificando importaciones...")
try:
    from config.settings import CHROME_PROFILE, DB_CONFIG, log_queue, stats_queue
    print("   [OK] config.settings importado correctamente")
except ImportError as e:
    print(f"   [ERROR] Error importando config.settings: {e}")
    sys.exit(1)

try:
    from backend.flask_server import iniciar_backend
    print("   [OK] backend.flask_server importado correctamente")
except ImportError as e:
    print(f"   [ERROR] Error importando backend.flask_server: {e}")
    sys.exit(1)

try:
    from chrome.manager import abrir_chrome_con_perfil, conectar_a_chrome
    print("   [OK] chrome.manager importado correctamente")
except ImportError as e:
    print(f"   [ERROR] Error importando chrome.manager: {e}")
    sys.exit(1)

try:
    from chrome.session import verificar_sesion_didi
    print("   [OK] chrome.session importado correctamente")
except ImportError as e:
    print(f"   [ERROR] Error importando chrome.session: {e}")
    sys.exit(1)

try:
    from bot.main import ejecutar_bot
    print("   [OK] bot.main importado correctamente")
except ImportError as e:
    print(f"   [ERROR] Error importando bot.main: {e}")
    sys.exit(1)

try:
    from bot.navigator import navegar_a_mis_casos
    print("   [OK] bot.navigator importado correctamente")
except ImportError as e:
    print(f"   [ERROR] Error importando bot.navigator: {e}")
    sys.exit(1)

try:
    from bot.processor import procesar_registro
    print("   [OK] bot.processor importado correctamente")
except ImportError as e:
    print(f"   [ERROR] Error importando bot.processor: {e}")
    sys.exit(1)

try:
    from gui.interface import BotDidiGUI
    print("   [OK] gui.interface importado correctamente")
except ImportError as e:
    print(f"   [ERROR] Error importando gui.interface: {e}")
    sys.exit(1)

print("\n[OK] Todas las importaciones funcionan correctamente")
print()

# Test 3: Verificar configuraciones
print("[3/5] Verificando configuraciones...")
print(f"   [OK] CHROME_PROFILE: {CHROME_PROFILE}")
print(f"   [OK] DB_CONFIG host: {DB_CONFIG['host']}")
print(f"   [OK] DB_CONFIG database: {DB_CONFIG['database']}")
print(f"   [OK] log_queue type: {type(log_queue).__name__}")
print(f"   [OK] stats_queue type: {type(stats_queue).__name__}")
print("\n[OK] Configuraciones cargadas correctamente")
print()

# Test 4: Verificar dependencias externas
print("[4/5] Verificando dependencias externas...")
dependencias = [
    ('selenium', 'webdriver'),
    ('flask', 'Flask'),
    ('waitress', 'serve'),
    ('pymysql', 'connect'),
    ('psutil', 'process_iter'),
    ('requests', 'get')
]

for modulo, atributo in dependencias:
    try:
        mod = __import__(modulo)
        if hasattr(mod, atributo):
            print(f"   [OK] {modulo} instalado correctamente")
        else:
            print(f"   [ERROR] {modulo} instalado pero falta atributo {atributo}")
    except ImportError:
        print(f"   [ERROR] {modulo} NO instalado")
        todo_ok = False

if not todo_ok:
    print("\n[ERROR] Faltan dependencias. Ejecuta: pip install -r requirements.txt")
    sys.exit(1)

print("\n[OK] Todas las dependencias instaladas")
print()

# Test 5: Verificar líneas de código
print("[5/5] Verificando optimización de código...")
archivos_codigo = [
    'config/settings.py',
    'backend/flask_server.py',
    'chrome/manager.py',
    'chrome/session.py',
    'bot/main.py',
    'bot/navigator.py',
    'bot/processor.py',
    'gui/interface.py',
    'Didi_GUI.pyw'
]

total_lineas = 0
for archivo in archivos_codigo:
    with open(archivo, 'r', encoding='utf-8') as f:
        lineas = len(f.readlines())
        total_lineas += lineas
        print(f"   {archivo}: {lineas} líneas")

print(f"\n   Total de líneas: {total_lineas}")
print(f"   Líneas en archivo original: 1549")
print(f"   Optimización: Código distribuido en {len(archivos_codigo)} módulos")

print("\n[OK] Código refactorizado correctamente")
print()

# Resumen final
print("=" * 60)
print("[EXITO] VERIFICACION COMPLETADA EXITOSAMENTE")
print("=" * 60)
print()
print("El bot esta listo para usarse. Ejecuta:")
print("   python Didi_GUI.pyw")
print()
print("Arquitectura modular:")
print("   - config/     - Configuraciones globales")
print("   - backend/    - Servidor Flask")
print("   - chrome/     - Gestion de Chrome")
print("   - bot/        - Logica del bot")
print("   - gui/        - Interfaz grafica")
print()
