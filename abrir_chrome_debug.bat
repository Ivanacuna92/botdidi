@echo off

:: Cambiar al directorio donde esta el script
cd /d "%~dp0"

echo ========================================
echo   ABRIR CHROME CON DEBUG HABILITADO
echo ========================================
echo.
echo Este Chrome mantendra tu sesion activa
echo para que el script de automatizacion
echo pueda trabajar SIN necesidad de login.
echo.
echo IMPORTANTE: Loguea en Didi y deja
echo este Chrome SIEMPRE ABIERTO.
echo.
echo ========================================
echo.

"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\Documents\Proyecto\ChromeProfile"
