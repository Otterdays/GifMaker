@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ========================================
echo  Gif-Maker — build desktop EXE
echo ========================================
echo.

REM Prefer project venv when present
set "PY=python"
if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
    echo Using venv: .venv
) else (
    echo Using system Python
)

"%PY%" --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install from https://python.org and retry.
    pause
    exit /b 1
)

REM Resolve real Desktop path (OneDrive-safe)
set "DESKTOP="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "[Environment]::GetFolderPath('Desktop')"`) do set "DESKTOP=%%I"
if not defined DESKTOP set "DESKTOP=%USERPROFILE%\Desktop"
if not exist "%DESKTOP%" (
    echo ERROR: Desktop folder not found: "%DESKTOP%"
    pause
    exit /b 1
)

echo Desktop: %DESKTOP%
echo.

echo [1/3] Installing runtime deps + PyInstaller...
"%PY%" -m pip install -r requirements.txt "pyinstaller>=6.0" -q
if errorlevel 1 (
    echo ERROR: pip install failed.
    pause
    exit /b 1
)

echo [2/3] Building GifMaker.exe (onefile, no console)...
if exist "build" rmdir /s /q "build" 2>nul
if exist "dist\GifMaker.exe" del /f /q "dist\GifMaker.exe" 2>nul

"%PY%" -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name "GifMaker" ^
  --paths "." ^
  --hidden-import=gif_maker ^
  --hidden-import=gif_maker.main ^
  --hidden-import=gif_maker.gui.main_window ^
  --hidden-import=gif_maker.core.gif_creator ^
  --hidden-import=gif_maker.core.quality_engine ^
  --hidden-import=gif_maker.utils.image_utils ^
  --hidden-import=gif_maker.utils.settings_store ^
  --hidden-import=gif_maker.utils.region_math ^
  --hidden-import=gif_maker.utils.window_picker ^
  --hidden-import=pyautogui ^
  --hidden-import=PIL ^
  --hidden-import=PIL.Image ^
  --hidden-import=pygetwindow ^
  "gif_maker\__main__.py"

if errorlevel 1 (
    echo ERROR: PyInstaller build failed.
    pause
    exit /b 1
)

if not exist "dist\GifMaker.exe" (
    echo ERROR: dist\GifMaker.exe missing after build.
    pause
    exit /b 1
)

echo [3/3] Copying to Desktop...
copy /Y "dist\GifMaker.exe" "%DESKTOP%\GifMaker.exe" >nul
if errorlevel 1 (
    echo ERROR: Could not copy EXE to Desktop.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Done.
echo  Desktop EXE: %DESKTOP%\GifMaker.exe
echo  Local copy:  %CD%\dist\GifMaker.exe
echo ========================================
echo.
pause
endlocal
exit /b 0
