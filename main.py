"""Entry point. Run with: python main.py

Before importing the game package we measure the user's display and shrink
the window to fit if it's smaller than the default 1000x1000 layout
(common on laptops). Settings.SCREEN_WIDTH/HEIGHT are patched at module
load time, so every downstream `from settings import SCREEN_WIDTH` picks
up the chosen size.
"""
import os
import sys

import pygame


def _ensure_assets_cwd():
    """When packaged with PyInstaller --onefile, sys._MEIPASS is the temp
    directory the bundle was extracted to. cwd is whatever the user ran
    the .exe from (usually Desktop / Downloads), so relative paths like
    "assets/images/foo.png" won't resolve. Pinning cwd to _MEIPASS makes
    every existing `os.path.join("assets", ...)` Just Work."""
    base = getattr(sys, "_MEIPASS", None)
    if base and os.path.isdir(base):
        os.chdir(base)


def _pick_screen_size() -> tuple[int, int]:
    """Largest square that fits the user's display, capped at 1000.
    Leaves ~80 px vertical margin for the OS taskbar + window chrome and
    ~40 px horizontal margin so the window isn't flush to the edges."""
    pygame.display.init()
    info = pygame.display.Info()
    avail_w = max(400, info.current_w - 40)
    avail_h = max(400, info.current_h - 80)
    side = min(1000, avail_w, avail_h)
    return side, side


if __name__ == "__main__":
    _ensure_assets_cwd()
    pygame.init()
    w, h = _pick_screen_size()
    import settings
    settings.SCREEN_WIDTH = w
    settings.SCREEN_HEIGHT = h
    settings.GRID_WIDTH = w // settings.TILE_SIZE
    settings.GRID_HEIGHT = h // settings.TILE_SIZE
    # Import App AFTER patching so its `from settings import SCREEN_WIDTH`
    # picks up the chosen values rather than the 1000 defaults.
    from game.app import App
    App().run()
