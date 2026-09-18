# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for WorkDay Tracker (onefile, windowed)."""

import sys
from pathlib import Path

block_cipher = None

project_root = Path(SPECPATH)
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

datas = [
    (str(src_path / "workday_tracker" / "theming" / "style.qss.tmpl"), "workday_tracker/theming"),
    (str(project_root / "assets" / "icon.ico"), "assets"),
]

a = Analysis(
    [str(project_root / "entrypoint.py")],
    pathex=[str(src_path)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name="WorkDayTracker",
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
    icon=str(project_root / "assets" / "icon.ico"),
)
