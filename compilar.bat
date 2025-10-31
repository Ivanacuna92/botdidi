@echo off
REM ============================================================================
REM Script de Compilación Automática - Bot Didi
REM ============================================================================
REM Este script compila el proyecto Python a un ejecutable .exe usando PyInstaller
REM
REM Uso: Simplemente haz doble clic en este archivo
REM ============================================================================

echo.
echo ============================================================================
echo                   BOT DIDI - COMPILACION A .EXE
echo ============================================================================
echo.

REM Verificar que estamos en la carpeta correcta
if not exist "Didi_GUI.pyw" (
    echo [ERROR] No se encontro Didi_GUI.pyw
    echo Este script debe ejecutarse en la carpeta raiz del proyecto
    pause
    exit /b 1
)

REM Verificar que PyInstaller este instalado
echo [1/5] Verificando PyInstaller...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [!] PyInstaller no esta instalado
    echo [*] Instalando PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] No se pudo instalar PyInstaller
        pause
        exit /b 1
    )
)
echo [OK] PyInstaller instalado

REM Opcional: Verificar si existe chromedriver.exe
echo.
echo [2/5] Verificando ChromeDriver...
if exist "chromedriver.exe" (
    echo [OK] chromedriver.exe encontrado - sera incluido en el .exe
    echo [*] Nota: Esto agregara ~15 MB al tamano final
) else (
    echo [!] chromedriver.exe NO encontrado
    echo [*] Intentaremos compilar SIN ChromeDriver primero
    echo [*] Si falla, descarga ChromeDriver de: https://googlechromelabs.github.io/chrome-for-testing/
)

REM Limpiar compilaciones anteriores
echo.
echo [3/5] Limpiando compilaciones anteriores...
if exist "build" (
    rmdir /s /q "build" 2>nul
    echo [OK] Carpeta build eliminada
)
if exist "dist" (
    rmdir /s /q "dist" 2>nul
    echo [OK] Carpeta dist eliminada
)

REM Compilar con PyInstaller
echo.
echo [4/5] Compilando con PyInstaller...
echo [*] Esto puede tomar 3-5 minutos, por favor espera...
echo.

python -m PyInstaller BotDidi.spec

if errorlevel 1 (
    echo.
    echo [ERROR] La compilacion fallo
    echo.
    echo Posibles causas:
    echo - Falta algun modulo de Python
    echo - Error en el codigo
    echo - Problema con PyInstaller
    echo.
    echo Revisa los mensajes de error arriba
    pause
    exit /b 1
)

REM Verificar que se creo el .exe
echo.
echo [5/5] Verificando resultado...
if not exist "dist\BotDidi.exe" (
    echo [ERROR] No se genero el archivo BotDidi.exe
    pause
    exit /b 1
)

REM Mostrar informacion del archivo
for %%I in (dist\BotDidi.exe) do (
    set tamano=%%~zI
    set /a tamanoMB=%%~zI / 1048576
)

echo.
echo ============================================================================
echo                        COMPILACION EXITOSA!
echo ============================================================================
echo.
echo Archivo generado: dist\BotDidi.exe
echo Tamano:           %tamanoMB% MB aproximadamente
echo.
echo SIGUIENTE PASO:
echo 1. Prueba el ejecutable: cd dist ^&^& BotDidi.exe
echo 2. Si funciona correctamente, puedes distribuirlo
echo 3. Los clientes solo necesitan BotDidi.exe (nada mas)
echo.
echo ARCHIVOS GENERADOS EN PRIMERA EJECUCION:
echo Los usuarios veran estos archivos creados automaticamente:
echo - C:\Users\[Usuario]\AppData\Roaming\BotDidi\DidiProfile\
echo - C:\Users\[Usuario]\AppData\Roaming\BotDidi\.license_token
echo - C:\Users\[Usuario]\AppData\Roaming\BotDidi\db_config.json
echo.
echo ============================================================================
echo.

pause
