@echo off
REM Build script for c0lor-mem (Windows)
REM Usage: scripts\build.bat

echo === c0lor-mem Build Script ===

REM Step 1: Build Python backend with PyInstaller
echo.
echo --- Building Python backend ---
cd /d "%~dp0..\python"

if not exist ".venv" (
    echo Creating Python virtual environment...
    python -m venv .venv
    .venv\Scripts\pip install -e ".[dev]"
)

.venv\Scripts\pip install pyinstaller 2>nul
.venv\Scripts\pyinstaller backend.spec --clean --noconfirm
echo Python backend built.

REM Step 2: Build Electron app
echo.
echo --- Building Electron app ---
cd /d "%~dp0.."

call npm run build

REM Step 3: Package with electron-builder
echo.
echo --- Packaging for Windows ---
call npx electron-builder --win

echo.
echo === Build complete! ===
echo Output: dist\
