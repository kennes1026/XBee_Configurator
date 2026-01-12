@echo off
chcp 65001 >nul
echo Starting XBee Configurator...
python xbee_configurator.py
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start. Please check if Python and dependencies are installed.
    echo Run: pip install -r requirements.txt
    pause
)
