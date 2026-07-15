from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _project_root() -> Path:
    # .../src/chemauto/core/reference_search_launcher.py -> project root
    return Path(__file__).resolve().parents[3]


def launch_reference_search() -> subprocess.Popen:
    """Launch the reference-search utility as a genuinely separate program."""
    candidates: list[tuple[list[str], int]] = []
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        frozen_candidates = [
            exe_dir / "ReferenceExplorer" / "ReferenceExplorer.exe",
            exe_dir / "ReferenceExplorer.exe",
            exe_dir / "Ref_search.exe",
            exe_dir / "Reference_Search.exe",
        ]
        for exe in frozen_candidates:
            if exe.is_file():
                candidates.append(([str(exe)], 0))
    else:
        root = _project_root()
        dev_exe = root / "tools" / "reference_explorer" / "dist" / "ReferenceExplorer.exe"
        if dev_exe.is_file():
            candidates.append(([str(dev_exe)], 0))
        script = root / "tools" / "reference_explorer" / "ReferenceExplorer.py"
        if script.is_file():
            pythonw = Path(sys.executable).with_name("pythonw.exe")
            launcher = pythonw if pythonw.is_file() else Path(sys.executable)
            candidates.append(([str(launcher), str(script)], creationflags if launcher.name.lower() != "pythonw.exe" else 0))

    if not candidates:
        raise FileNotFoundError(
            "Reference Search was not found. Build tools/reference_explorer/ReferenceExplorer.spec "
            "or keep ReferenceExplorer.exe beside ChemAuto.exe."
        )
    command, flags = candidates[0]
    return subprocess.Popen(command, creationflags=flags)
