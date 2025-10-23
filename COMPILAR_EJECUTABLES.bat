@echo off
setlocal

:: Cambiar al directorio donde esta el script
cd /d "%~dp0"

echo =========================================================
echo      Compilar Scripts a Ejecutables (.exe)
echo =========================================================
echo.
echo ADVERTENCIA: Este proceso puede tardar 5-10 minutos
echo.
pause

:: Limpiar compilaciones anteriores
if exist "dist" rmdir /S /Q dist
if exist "build" rmdir /S /Q build
if exist "*.spec" del /Q *.spec

echo.
echo [1/4] Compilando Didi.exe...
echo -------------------------------------------------------
python -m PyInstaller --onefile --noconsole --icon=NONE ^
    --name=Didi ^
    --add-data "requirements.txt;." ^
    Didi.py

if errorlevel 1 (
    echo [ERROR] Error al compilar Didi.exe
    pause
    exit /b 1
)
echo [OK] Didi.exe compilado

echo.
echo [2/4] Compilando backend_conteo.exe...
echo -------------------------------------------------------
python -m PyInstaller --onefile --console ^
    --name=backend_conteo ^
    backend_conteo.py

if errorlevel 1 (
    echo [ERROR] Error al compilar backend_conteo.exe
    pause
    exit /b 1
)
echo [OK] backend_conteo.exe compilado

echo.
echo [3/4] Compilando ver_datos.exe...
echo -------------------------------------------------------
python -m PyInstaller --onefile --console ^
    --name=ver_datos ^
    ver_datos.py

if errorlevel 1 (
    echo [ERROR] Error al compilar ver_datos.exe
    pause
    exit /b 1
)
echo [OK] ver_datos.exe compilado

echo.
echo [4/4] Compilando test_conexion.exe...
echo -------------------------------------------------------
python -m PyInstaller --onefile --console ^
    --name=test_conexion ^
    test_conexion.py

if errorlevel 1 (
    echo [ERROR] Error al compilar test_conexion.exe
    pause
    exit /b 1
)
echo [OK] test_conexion.exe compilado

echo.
echo =========================================================
echo.
echo [OK] Todos los ejecutables compilados exitosamente
echo.
echo Archivos generados en: dist\
echo   - Didi.exe
echo   - backend_conteo.exe
echo   - ver_datos.exe
echo   - test_conexion.exe
echo.
echo Tamano aproximado: ~150-200 MB
echo.
echo =========================================================
echo.
pause
