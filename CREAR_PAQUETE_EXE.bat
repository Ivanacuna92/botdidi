@echo off
cd /d "%~dp0"

echo =========================================================
echo      Crear Paquete de Distribucion (Ejecutables)
echo =========================================================
echo.

set CARPETA_DESTINO=BotDidi_Ejecutable_v1.0
set ARCHIVO_ZIP=BotDidi_Ejecutable_v1.0.zip

echo [*] Verificando ejecutables...

if not exist "dist\Didi.exe" goto error_didi
if not exist "dist\backend_conteo.exe" goto error_backend

echo [OK] Ejecutables encontrados
echo.
goto continuar

:error_didi
echo.
echo [ERROR] No se encontro Didi.exe
echo.
echo Debes compilar los ejecutables primero:
echo    1. Ejecuta: COMPILAR_EJECUTABLES.bat
echo    2. Espera a que termine (5-10 minutos)
echo    3. Vuelve a ejecutar este script
echo.
pause
exit /b 1

:error_backend
echo [ERROR] No se encontro backend_conteo.exe
echo    Ejecuta COMPILAR_EJECUTABLES.bat primero
pause
exit /b 1

:continuar

if exist "%CARPETA_DESTINO%" (
    echo [*] Eliminando carpeta anterior...
    rmdir /S /Q "%CARPETA_DESTINO%"
)

echo [*] Creando carpeta de distribucion...
mkdir "%CARPETA_DESTINO%"

echo [*] Copiando archivos de inicio...
copy "INSTALAR_EXE.bat" "%CARPETA_DESTINO%\INSTALAR.bat" >nul
copy "INICIAR_BOT_EXE.bat" "%CARPETA_DESTINO%\INICIAR_BOT.bat" >nul
copy "VER_ESTADISTICAS_EXE.bat" "%CARPETA_DESTINO%\VER_ESTADISTICAS.bat" >nul
copy "abrir_chrome_debug.bat" "%CARPETA_DESTINO%\" >nul

echo [*] Copiando ejecutables...
copy "dist\Didi.exe" "%CARPETA_DESTINO%\" >nul
copy "dist\backend_conteo.exe" "%CARPETA_DESTINO%\" >nul
copy "dist\ver_datos.exe" "%CARPETA_DESTINO%\" >nul
copy "dist\test_conexion.exe" "%CARPETA_DESTINO%\" >nul

echo [*] Copiando documentacion...
if exist "INSTRUCCIONES_USUARIO_FINAL.txt" copy "INSTRUCCIONES_USUARIO_FINAL.txt" "%CARPETA_DESTINO%\INSTRUCCIONES_USUARIO.txt" >nul
if exist "INSTRUCCIONES.txt" copy "INSTRUCCIONES.txt" "%CARPETA_DESTINO%\" >nul

echo [OK] Archivos copiados
echo.

echo [*] Creando README...
echo =========================================================> "%CARPETA_DESTINO%\LEEME_PRIMERO.txt"
echo  BOT DIDI - INICIO RAPIDO>> "%CARPETA_DESTINO%\LEEME_PRIMERO.txt"
echo =========================================================>> "%CARPETA_DESTINO%\LEEME_PRIMERO.txt"
echo.>> "%CARPETA_DESTINO%\LEEME_PRIMERO.txt"
echo Esta version NO requiere instalar Python>> "%CARPETA_DESTINO%\LEEME_PRIMERO.txt"
echo Todo esta listo para usarse directamente>> "%CARPETA_DESTINO%\LEEME_PRIMERO.txt"
echo.>> "%CARPETA_DESTINO%\LEEME_PRIMERO.txt"
echo PASOS:>> "%CARPETA_DESTINO%\LEEME_PRIMERO.txt"
echo.>> "%CARPETA_DESTINO%\LEEME_PRIMERO.txt"
echo 1. Doble clic en: INSTALAR.bat>> "%CARPETA_DESTINO%\LEEME_PRIMERO.txt"
echo 2. Lee: INSTRUCCIONES_USUARIO.txt>> "%CARPETA_DESTINO%\LEEME_PRIMERO.txt"
echo 3. Ejecuta: abrir_chrome_debug.bat (primera vez)>> "%CARPETA_DESTINO%\LEEME_PRIMERO.txt"
echo 4. Usa el bot: INICIAR_BOT.bat>> "%CARPETA_DESTINO%\LEEME_PRIMERO.txt"
echo 5. Ver resultados: VER_ESTADISTICAS.bat>> "%CARPETA_DESTINO%\LEEME_PRIMERO.txt"
echo.>> "%CARPETA_DESTINO%\LEEME_PRIMERO.txt"
echo =========================================================>> "%CARPETA_DESTINO%\LEEME_PRIMERO.txt"

echo [OK] README creado
echo.

echo [*] Creando archivo ZIP...
powershell -command "Compress-Archive -Path '%CARPETA_DESTINO%' -DestinationPath '%ARCHIVO_ZIP%' -Force" 2>nul

if exist "%ARCHIVO_ZIP%" (
    echo [OK] Archivo ZIP creado: %ARCHIVO_ZIP%
) else (
    echo [AVISO] No se pudo crear el ZIP
    echo    La carpeta "%CARPETA_DESTINO%" esta lista para distribuir
)

echo.
echo =========================================================
echo [OK] PAQUETE LISTO
echo =========================================================
echo.
echo Carpeta: %CARPETA_DESTINO%
if exist "%ARCHIVO_ZIP%" echo ZIP: %ARCHIVO_ZIP%
echo.
echo Contenido:
echo  - Ejecutables (.exe)
echo  - Scripts de inicio (.bat)
echo  - Documentacion
echo.
echo NO requiere Python instalado
echo.
echo =========================================================
echo.
pause
