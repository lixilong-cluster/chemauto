# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller onedir specification for ChemAuto 7.1.2.

This spec intentionally resolves every path from CHEMAUTO_PROJECT_ROOT (set by
build_chemauto_portable.bat) or from the current working directory.  It does
not depend on PyInstaller's SPECPATH semantics.
"""
from pathlib import Path
import os

ROOT = Path(os.environ.get("CHEMAUTO_PROJECT_ROOT", os.getcwd())).resolve()
SRC = ROOT / "src"
ENTRY = ROOT / "build_cli.py"

if not ENTRY.is_file():
    raise SystemExit(f"ChemAuto entry script not found: {ENTRY}")
if not (SRC / "chemauto" / "__init__.py").is_file():
    raise SystemExit(f"ChemAuto source package not found under: {SRC}")


def add_tree(root: Path, package_root: Path, datas, binaries, hiddenimports):
    """Collect a bundled Python package without importing optional GUI plugins."""
    for path in root.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        rel = path.relative_to(package_root)
        # The Excel renderer uses the headless PyMOL command API only.  The
        # optional pmg_tk/plugins GUI is deliberately not bundled.
        if rel.parts[:2] == ("pymol", "plugins") or "pmg_tk" in rel.parts:
            continue
        suffix = path.suffix.lower()
        if suffix == ".py":
            module = ".".join(rel.with_suffix("").parts)
            if module.endswith(".__init__"):
                module = module[:-9]
            if module:
                hiddenimports.append(module)
        elif suffix in {".pyd", ".dll"}:
            binaries.append((str(path), str(rel.parent)))
        elif suffix not in {".pyc", ".pyo"}:
            datas.append((str(path), str(rel.parent)))


datas = [
    (str(SRC / "chemauto/resources/DOS-default.otpu"), "chemauto/resources"),
    (str(SRC / "chemauto/resources/chk_remote_formchk_v7_direct_simple.ps1"), "chemauto/resources"),
    (str(SRC / "chemauto/resources/chemauto.ico"), "chemauto/resources"),
]
binaries = []
hiddenimports = [
    "chemauto.cli",
    "chemauto.features.analyzer", "chemauto.features.extractor",
    "chemauto.features.generator", "chemauto.features.pes_exporter",
    "chemauto.features.dos_plotter", "chemauto.features.xyz_converter",
    "chemauto.features.term_gen",
    "chemauto.gui.log_browser", "chemauto.gui.remote_formchk_dialog",
    "chemauto.gui.preferences_dialog", "chemauto.gui.term_dialog",
    "chemauto.gui.pes_dialog", "chemauto.gui.dos_dialog",
    "chemauto.gui.vde_ade_dialog", "chemauto.gui.vde_ade_generator_dialog",
    "chemauto.gui.excel_structures_dialog", "chemauto.gui.gjf_editor_dialog",
    "chemauto.gui.xyz_viewer_dialog", "chemauto.gui.widgets",
    "chemauto.core.related_files", "chemauto.core.gjf_stability",
    "chemauto.core.gjf_template", "chemauto.core.fchk_xyz",
    "chemauto.core.remote_formchk", "chemauto.core.dos_pairs",
    "chemauto.core.vde_ade", "chemauto.core.vde_ade_generator",
    "chemauto.core.external_open", "chemauto.core.excel_structures",
    "chemauto.core.gjf_document", "chemauto.core.xyz_frames",
    "chemauto.core.record_sorting", "chemauto.core.reference_search_launcher",
    "pyqtgraph.opengl", "OpenGL.GL", "PIL.Image", "PIL.ImageQt",
]

# Bundle the original ChemAuto 5.3 PyMOL backend without importing its optional
# Tk plugin system during the PyInstaller analysis stage.
pymol_root = SRC / "pymol"
if pymol_root.is_dir():
    add_tree(pymol_root, SRC, datas, binaries, hiddenimports)
    # The historical ChemAuto 6.0 distribution placed the Microsoft OpenMP
    # runtime at the application-library root. Keep that layout in addition to
    # the package-local copy so Windows can resolve _cmd.pyd consistently.
    vcomp = pymol_root / "VCOMP140.DLL"
    if vcomp.is_file():
        binaries.append((str(vcomp), "."))

# De-duplicate while keeping deterministic order.
hiddenimports = list(dict.fromkeys(hiddenimports))
datas = list(dict.fromkeys(datas))
binaries = list(dict.fromkeys(binaries))

a = Analysis(
    [str(ENTRY)],
    pathex=[str(SRC)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PyQt5", "PySide6", "IPython", "torch", "scipy", "pmg_tk", "pymol.plugins"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ChemAuto",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    icon=[str(ROOT / "assets/icons/chemauto.ico")],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="ChemAuto_Portable",
)
