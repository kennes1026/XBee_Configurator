@echo off
chcp 65001 >nul
echo ========================================
echo XBee Configurator - Build Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if PyInstaller is installed
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing PyInstaller...
    pip install pyinstaller
)

REM Check if required packages are installed
echo [INFO] Checking dependencies...
pip install -r requirements.txt

echo.
echo [INFO] Building executable...
echo.

REM Build with PyInstaller (using python -m to avoid PATH issues)
python -m PyInstaller --noconfirm --onefile --windowed ^
    --name "XBee_Configurator" ^
    --add-data "README.md;." ^
    xbee_configurator.py

echo.
if exist "dist\XBee_Configurator.exe" (
    echo ========================================
    echo [SUCCESS] Build completed!
    echo Executable: dist\XBee_Configurator.exe
    echo ========================================
) else (
    echo [ERROR] Build failed!
)

echo.
pause
