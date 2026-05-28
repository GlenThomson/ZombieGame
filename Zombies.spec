# PyInstaller spec file — produces dist/Zombies.exe.
#
# Build with:  .venv\Scripts\python.exe -m PyInstaller Zombies.spec --noconfirm
# Or just run: build_exe.bat
#
# Bundles all images, sounds, and shipped .pkl maps so the exe is fully
# self-contained. Single-file mode (`onefile=True`) means the player
# double-clicks one Zombies.exe and that's it.

# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files

# Every non-code file the game opens at runtime. PyInstaller doesn't see
# them via static analysis so they need to be enumerated.
datas = [
    ("assets/images", "assets/images"),
    ("assets/images/tiles", "assets/images/tiles"),
    ("assets/images/decor", "assets/images/decor"),
    ("assets/sounds", "assets/sounds"),
    ("maps", "maps"),
]

# pygame's mixer + display modules sometimes need hidden imports on
# Windows. Add anything you see in the build log under "ImportError" here.
hiddenimports = []


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Trim build size: nothing we ship uses these. (tkinter stays —
        # the map editor's Save/Open dialogs need it.)
        'unittest',
        'pydoc',
        'doctest',
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Zombies',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,         # GUI app: no console window pops up alongside
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
