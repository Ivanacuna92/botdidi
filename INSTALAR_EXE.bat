@echo off
setlocal enabledelayedexpansion

:: Cambiar al directorio donde esta el script
cd /d "%~dp0"

echo =========================================================
echo      Bot Didi - Instalador (Version Ejecutable)
echo =========================================================
echo.
echo Esta version NO requiere instalar Python
echo Todo esta listo para usarse
echo.

:: Verificar Chrome
echo [1/2] Verificando Google Chrome...
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    echo [OK] Chrome instalado
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    echo [OK] Chrome instalado
) else (
    echo [ADVERTENCIA] Chrome no encontrado en la ruta estandar
    echo   El bot podria no funcionar correctamente
    echo.
    echo Por favor instala Google Chrome desde:
    echo https://www.google.com/chrome/
    echo.
    pause
)

:: Verificar conexión a base de datos
echo.
echo [2/2] Verificando conexion a base de datos...
if exist "test_conexion.exe" (
    test_conexion.exe >nul 2>&1
    if errorlevel 1 (
        echo [ADVERTENCIA] No se pudo conectar a la base de datos
        echo   El sistema de monitoreo podria no funcionar
        echo   Verifica tu conexion a internet
        pause
    ) else (
        echo [OK] Conexion a base de datos OK
    )
) else (
    echo [OK] Archivo de prueba no encontrado, continuando...
)

echo.
echo =========================================================
echo.
echo [OK] Instalacion completada exitosamente!
echo.
echo IMPORTANTE: Esta version NO requiere Python
echo Todos los archivos necesarios estan incluidos
echo.
echo SIGUIENTES PASOS:
echo   1. Lee el archivo: INSTRUCCIONES_USUARIO.txt
echo   2. Ejecuta: INICIAR_BOT.bat
echo.
echo =========================================================
echo.
pause
