@echo off
chcp 65001 >nul
title Bot Didi GUI - Instalador

color 0A
echo ========================================
echo    BOT DIDI - INSTALADOR GUI
echo ========================================
echo.

:: Verificar Python
echo [1/4] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo [ERROR] Python no esta instalado
    echo.
    echo Por favor instala Python desde:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
echo [OK] Python encontrado
echo.

:: Verificar pip
echo [2/4] Verificando pip...
pip --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo [ERROR] pip no esta instalado
    echo.
    pause
    exit /b 1
)
echo [OK] pip encontrado
echo.

:: Instalar dependencias
echo [3/4] Instalando dependencias...
echo [*] Esto puede tomar varios minutos...
echo.
pip install -r requirements.txt
if errorlevel 1 (
    color 0C
    echo.
    echo [ERROR] No se pudieron instalar las dependencias
    echo.
    pause
    exit /b 1
)
echo.
echo [OK] Dependencias instaladas
echo.

:: Verificar Chrome
echo [4/4] Verificando Google Chrome...
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    echo [OK] Chrome encontrado
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    echo [OK] Chrome encontrado
) else (
    color 0E
    echo [ADVERTENCIA] Chrome no encontrado en ubicacion estandar
    echo El bot intentara encontrarlo automaticamente
)
echo.

:: Verificar base de datos (opcional)
echo [*] Verificando conexion a base de datos...
python -c "import pymysql; conn = pymysql.connect(host='datenbanken.aloia.dev', port=3306, user='aloiaMariaDB', password='', database='DidiMonitoreo', connect_timeout=5); print('[OK] Conexion exitosa'); conn.close()" 2>nul
if errorlevel 1 (
    color 0E
    echo [ADVERTENCIA] No se pudo conectar a la base de datos
    echo El bot funcionara, pero no guardara estadisticas
    echo Verifica tu conexion a internet
)
echo.

:: Éxito
color 0A
echo ========================================
echo    INSTALACION COMPLETADA
echo ========================================
echo.
echo Todo listo para usar el bot!
echo.
echo Para iniciar el bot:
echo   1. Doble click en: EJECUTAR_BOT_GUI.bat
echo   2. Click en boton "INICIAR BOT"
echo   3. Listo!
echo.
echo Lee el archivo LEEME_GUI.txt para mas informacion.
echo.
pause
