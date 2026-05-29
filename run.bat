@echo off
REM One-click launcher for Windows.
REM
REM First run: creates .venv and installs pygame.
REM Subsequent runs: just launches the game.

setlocal

if not exist .venv (
    echo First run: setting up .venv and installing pygame...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo Could not create .venv. Make sure Python 3.10+ is installed
        echo and on your PATH ^(https://www.python.org/downloads^).
        pause
        exit /b 1
    )
    .venv\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo pip install failed. Check the log above.
        pause
        exit /b 1
    )
)

.venv\Scripts\python.exe main.py
