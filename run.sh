#!/usr/bin/env bash
# One-click launcher for macOS / Linux. Mirror of run.bat.
#
# First run: creates .venv and installs pygame.
# Subsequent runs: just launches the game.
#
# If "python3" isn't on your PATH, install it from python.org (Mac) or
# your distro's package manager (Linux). The game needs Python 3.10+.

set -e

cd "$(dirname "$0")"

PY=python3
if ! command -v "$PY" >/dev/null 2>&1; then
    PY=python
fi

if [ ! -d .venv ]; then
    echo "First run: setting up .venv and installing pygame..."
    "$PY" -m venv .venv
    .venv/bin/python -m pip install --upgrade pip >/dev/null
    .venv/bin/python -m pip install -r requirements.txt
fi

exec .venv/bin/python main.py
