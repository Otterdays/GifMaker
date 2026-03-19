@echo off
echo Starting Gif-Maker V1.0...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Check if packages are installed
python -c "import pyautogui, PIL" >nul 2>&1
if errorlevel 1 (
    echo Required packages not found. Running installer...
    call install.bat
    if errorlevel 1 (
        echo Installation failed. Please run install.bat manually
        pause
        exit /b 1
    )
)

REM Launch the application
python -m gif_maker

pause
