@echo off
setlocal

:: Cambiar al directorio donde esta el script
cd /d "%~dp0"

echo =========================================================
echo      Bot Didi - Iniciador Automatico
echo =========================================================
echo.

:: Verificar si el backend ya está corriendo
tasklist /FI "IMAGENAME eq backend_conteo.exe" 2>nul | find /I /N "backend_conteo.exe">nul
if "%ERRORLEVEL%"=="0" (
    echo [OK] El backend ya esta corriendo
) else (
    echo [*] Iniciando backend en segundo plano...
    if exist "backend_conteo.exe" (
        start "Backend - Bot Didi" /MIN backend_conteo.exe
        timeout /t 3 >nul
        echo [OK] Backend iniciado
    ) else (
        echo [ERROR] No se encontro backend_conteo.exe
        echo    Verifica que todos los archivos esten en la carpeta
        pause
        exit /b 1
    )
)

echo.
echo =========================================================
echo.
echo IMPORTANTE:
echo   1. Asegurate de tener Chrome abierto con:
echo      abrir_chrome_debug.bat
echo.
echo   2. Ya debes estar logueado en Didi en ese Chrome
echo.
echo =========================================================
echo.
set /p continuar="Continuar con la ejecucion del bot? (S/N): "

if /i "%continuar%"=="S" (
    echo.
    echo [*] Ejecutando bot...
    echo.
    if exist "Didi.exe" (
        Didi.exe
    ) else (
        echo [ERROR] No se encontro Didi.exe
        echo    Verifica que todos los archivos esten en la carpeta
        pause
        exit /b 1
    )
) else (
    echo.
    echo Operacion cancelada
)

echo.
pause
