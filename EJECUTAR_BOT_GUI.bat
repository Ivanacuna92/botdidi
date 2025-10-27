@echo off
chcp 65001 >nul
title Bot Didi - Lanzador GUI

echo ========================================
echo    BOT DIDI - VERSION CON INTERFAZ
echo ========================================
echo.
echo [*] Iniciando interfaz grafica...
echo.

python Didi_GUI.py

if errorlevel 1 (
    echo.
    echo [ERROR] No se pudo ejecutar el bot.
    echo.
    echo Posibles soluciones:
    echo 1. Asegurate de tener Python instalado
    echo 2. Ejecuta: pip install -r requirements.txt
    echo.
    pause
)
