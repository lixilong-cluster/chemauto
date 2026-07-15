from __future__ import annotations

import sys
import tempfile
from pathlib import Path


def main() -> int:
    project = Path(__file__).resolve().parents[1]
    src = project / "src"
    sys.path.insert(0, str(src))

    from chemauto.core.excel_structures import render_xyz_png_pymol

    xyz = """4
ChemAuto source PyMOL smoke test
C   0.000000   0.000000   0.000000
O   1.160000   0.000000   0.000000
H  -0.580000   0.920000   0.000000
H  -0.580000  -0.920000   0.000000
"""
    with tempfile.TemporaryDirectory(prefix="chemauto_pymol_check_") as td:
        output = Path(td) / "pymol_source_smoke.png"
        try:
            render_xyz_png_pymol(xyz, output)
        except Exception as exc:
            print(f"[FAILED] Bundled PyMOL source renderer: {type(exc).__name__}: {exc}")
            return 21
        if not output.is_file() or output.stat().st_size < 512:
            print(f"[FAILED] Bundled PyMOL did not create a valid PNG: {output}")
            return 22
        print(f"[OK] Bundled PyMOL source renderer produced a PNG ({output.stat().st_size} bytes).")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
