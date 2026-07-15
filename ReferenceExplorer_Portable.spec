# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import os

ROOT = Path(os.environ.get("CHEMAUTO_PROJECT_ROOT", os.getcwd())).resolve()
REF = ROOT / "tools" / "reference_explorer"
ENTRY = REF / "ReferenceExplorer.py"
if not ENTRY.is_file():
    raise SystemExit(f"Reference Explorer entry script not found: {ENTRY}")

a = Analysis(
    [str(ENTRY)],
    pathex=[str(REF)],
    binaries=[],
    datas=[(str(REF / "search.ico"), ".")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PyQt6", "PySide6"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ReferenceExplorer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=[str(REF / "search.ico")],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="ReferenceExplorer_Portable",
)
