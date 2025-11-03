# -*- mode: python ; coding: utf-8 -*-

"""
Configuración de PyInstaller para Bot Didi

Este archivo define cómo PyInstaller empaquetará la aplicación en un .exe

Características:
- Ejecutable de un solo archivo (--onefile)
- Sin ventana de consola (--windowed)
- Incluye todos los módulos necesarios
- NO incluye ChromeDriver por defecto (intentaremos sin él primero)
"""

block_cipher = None

a = Analysis(
    ['Didi_GUI.pyw'],  # Archivo principal de entrada
    pathex=[],
    binaries=[],
    datas=[
        # Si necesitas incluir ChromeDriver, descomenta la siguiente línea:
        # ('chromedriver.exe', '.'),

        # Otros archivos que quieras incluir (iconos, recursos, etc.)
    ],
    hiddenimports=[
        # Módulos que PyInstaller no detecta automáticamente
        'pymysql',
        'pymysql.cursors',
        'cryptography',
        'cryptography.fernet',
        'flask',
        'flask_cors',
        'waitress',
        'selenium',
        'selenium.webdriver',
        'selenium.webdriver.chrome',
        'selenium.webdriver.chrome.service',
        'selenium.webdriver.chrome.options',
        'selenium.webdriver.common.by',
        'selenium.webdriver.support',
        'selenium.webdriver.support.ui',
        'selenium.webdriver.support.expected_conditions',
        'bcrypt',
        'jwt',
        'psutil',
        'requests',
        'tkinter',
        'queue',
        'threading',
        'json',
        'base64',
        'hashlib',
        'secrets',
        'platform',
        'uuid',
        'subprocess',
        'csv',
        'datetime',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Excluir módulos innecesarios para reducir tamaño
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BotDidi',  # Nombre del ejecutable
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Desactivar UPX para evitar falsos positivos de antivirus
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Sin ventana de consola (solo GUI)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Si tienes un icono .ico, ponlo aquí: icon='icono.ico'
)
