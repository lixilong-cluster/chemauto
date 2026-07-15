from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from chemauto.infra.config import load_user_config

WINDOWS_NOTEPAD = "__WINDOWS_NOTEPAD__"
SYSTEM_DEFAULT = "__SYSTEM_DEFAULT__"


def windows_notepad_path() -> str:
    if os.name != "nt":
        return ""
    windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
    candidates = [windir / "System32" / "notepad.exe", windir / "notepad.exe"]
    for path in candidates:
        if path.is_file():
            return str(path)
    found = shutil.which("notepad.exe")
    return found or ""


def detect_gaussview() -> str:
    """Find a likely GaussView executable without requiring registry knowledge."""
    if os.name != "nt":
        return ""
    roots = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
        Path(r"C:\G16W"), Path(r"C:\G09W"),
    ]
    patterns = ["GaussView*.exe", "gview.exe", "gv.exe"]
    direct = [
        Path(r"C:\G16W\gview.exe"), Path(r"C:\G09W\gview.exe"),
    ]
    for path in direct:
        if path.is_file():
            return str(path)
    for root in roots:
        if not root.exists():
            continue
        for sub in (root, root / "Gaussian", root / "GaussView", root / "Gaussian" / "GaussView6"):
            if not sub.exists():
                continue
            for pattern in patterns:
                matches = list(sub.rglob(pattern))
                if matches:
                    return str(matches[0])
    return ""


def _configured_executable_for(path: Path) -> str:
    cfg = load_user_config()
    suffix = path.suffix.lower()
    if suffix in {'.log', '.out'}:
        return str(cfg.get('log_viewer_path', SYSTEM_DEFAULT) or SYSTEM_DEFAULT)
    if suffix in {'.gjf', '.com', '.txt'}:
        return str(cfg.get('text_editor_path', WINDOWS_NOTEPAD) or WINDOWS_NOTEPAD)
    if suffix in {'.fchk', '.fch'}:
        return str(cfg.get('fchk_viewer_path', SYSTEM_DEFAULT) or SYSTEM_DEFAULT)
    if suffix == '.xyz':
        return str(cfg.get('xyz_viewer_path', SYSTEM_DEFAULT) or SYSTEM_DEFAULT)
    return SYSTEM_DEFAULT


def can_open_related(path: str | Path) -> bool:
    p = Path(path)
    return p.suffix.lower() != '.chk'


def open_external(path: str | Path, executable: Optional[str] = None) -> None:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    if p.suffix.lower() == '.chk':
        raise ValueError('Gaussian binary .chk files are not opened directly. Use .chk → .fchk instead.')

    exe = (executable or _configured_executable_for(p)).strip().strip('"')
    if exe == WINDOWS_NOTEPAD:
        exe = windows_notepad_path()
        if not exe:
            raise FileNotFoundError("Windows Notepad could not be located.")
    if exe == SYSTEM_DEFAULT:
        exe = ""

    if exe:
        exe_path = Path(exe)
        if not exe_path.is_file():
            raise FileNotFoundError(f'Configured application does not exist: {exe_path}')
        subprocess.Popen([str(exe_path), str(p)])
        return

    if os.name == 'nt':
        os.startfile(str(p))  # type: ignore[attr-defined]
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', str(p)])
    else:
        subprocess.Popen(['xdg-open', str(p)])
