@echo off
setlocal

:: Cambiar al directorio donde esta el script
cd /d "%~dp0"

:menu
cls
echo =========================================================
echo      Bot Didi - Ver Estadisticas
echo =========================================================
echo.
echo [1] Ver clientes procesados HOY
echo [2] Ver estadisticas de los ultimos 7 dias
echo [3] Ver estadisticas de los ultimos 30 dias
echo [4] Ver todos los datos
echo [0] Salir
echo.
set /p opcion="Selecciona una opcion: "

if "%opcion%"=="1" goto hoy
if "%opcion%"=="2" goto semana
if "%opcion%"=="3" goto mes
if "%opcion%"=="4" goto todos
if "%opcion%"=="0" goto fin
goto menu

:hoy
cls
echo =========================================================
echo  CLIENTES PROCESADOS HOY
echo =========================================================
echo.
if exist "ver_datos.exe" (
    ver_datos.exe
) else (
    echo [ERROR] No se encontro ver_datos.exe
)
echo.
pause
goto menu

:semana
cls
echo =========================================================
echo  ESTADISTICAS - ULTIMOS 7 DIAS
echo =========================================================
echo.
echo Consultando backend...
echo.
curl -s "http://localhost:5000/estadisticas?dias=7" 2>nul
if errorlevel 1 (
    echo [ERROR] No se pudo conectar al backend
    echo    Asegurate de que el backend este corriendo
    echo    (Se inicia automaticamente con INICIAR_BOT.bat)
)
echo.
echo.
pause
goto menu

:mes
cls
echo =========================================================
echo  ESTADISTICAS - ULTIMOS 30 DIAS
echo =========================================================
echo.
echo Consultando backend...
echo.
curl -s "http://localhost:5000/estadisticas?dias=30" 2>nul
if errorlevel 1 (
    echo [ERROR] No se pudo conectar al backend
    echo    Asegurate de que el backend este corriendo
)
echo.
echo.
pause
goto menu

:todos
cls
echo =========================================================
echo  TODOS LOS DATOS
echo =========================================================
echo.
if exist "ver_datos.exe" (
    ver_datos.exe
) else (
    echo [ERROR] No se encontro ver_datos.exe
)
echo.
pause
goto menu

:fin
exit /b 0
