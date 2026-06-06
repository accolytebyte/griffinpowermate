@echo off
REM Installation script for PowerMate from source

echo Installing PowerMate...
echo.

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3.11+ is not installed or not in PATH
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

echo Installing dependencies from requirements.txt...
pip install -r requirements.txt

if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    echo Check your internet connection and try again
    pause
    exit /b 1
)

echo.
echo Installation complete!
echo.
echo Next steps:
echo 1. Install libusb-win32 driver via Zadig:
echo    - Download from https://zadig.akeo.ie/
echo    - Plug in PowerMate
echo    - In Zadig: Options > List All Devices > Select Griffin PowerMate > Replace Driver
echo.
echo 2. Run the app:
echo    python main.py
echo.
pause
