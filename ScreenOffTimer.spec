# PyInstaller spec — build on Windows 10: pyinstaller ScreenOffTimer.spec
# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None
root = Path(SPECPATH)
src = root / "src"
icon = root / "data" / "icons" / "screen-off-timer.ico"
if not icon.is_file():
    icon = root / "data" / "icons" / "hicolor" / "256x256" / "apps" / "screen-off-timer.png"

datas = []
ico = root / "data" / "icons" / "screen-off-timer.ico"
if ico.is_file():
    datas.append((str(ico), "data/icons"))

a = Analysis(
    [str(src / "run.py")],
    pathex=[str(src)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["gi", "gi.repository"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="ScreenOffTimer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon) if icon.suffix.lower() == ".ico" else None,
)
