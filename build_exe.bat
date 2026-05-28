@echo off
REM Build a standalone Zombies.exe that doesn't need Python or any
REM dependencies installed on the player's PC.
REM
REM Output: dist\Zombies.exe (single file, ~30-60 MB)
REM
REM Just run this from the project root after a clean clone:
REM   build_exe.bat

setlocal

if not exist .venv (
    echo No .venv found. Create one first:
    echo   python -m venv .venv
    echo   .venv\Scripts\python.exe -m pip install pygame pyinstaller
    exit /b 1
)

REM Make sure PyInstaller is installed in the venv
.venv\Scripts\python.exe -c "import PyInstaller" 2>NUL
if errorlevel 1 (
    echo Installing PyInstaller...
    .venv\Scripts\python.exe -m pip install pyinstaller
)

REM Clean previous build artifacts so we get a fresh exe every time.
if exist build rmdir /s /q build
if exist dist\Zombies.exe del /q dist\Zombies.exe

.venv\Scripts\python.exe -m PyInstaller Zombies.spec --noconfirm

if exist dist\Zombies.exe (
    echo.
    echo ============================================================
    echo  Built: dist\Zombies.exe
    echo  Send this single file to anyone — they can double-click it.
    echo ============================================================
) else (
    echo.
    echo Build failed. Check the log above for errors.
    exit /b 1
)
