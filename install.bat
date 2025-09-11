@echo off
echo Installing Gif-Maker V1.0 dependencies...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo Python found. Installing packages...
echo.

REM Install required packages
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERROR: Failed to install packages
    echo Please check your internet connection and try again
    pause
    exit /b 1
)

echo.
echo Installation completed successfully!
echo You can now run launch.bat to start Gif-Maker V1.0
pause
