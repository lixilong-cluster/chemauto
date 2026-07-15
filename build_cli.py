from __future__ import annotations

import sys
from pathlib import Path


def _pymol_self_test() -> int:
    """Render a tiny molecule with the legacy PyMOL backend.

    This command is used both before and after PyInstaller packaging. A build is
    only reported as successful when the requested PNG is actually produced.
    """
    from chemauto.core.excel_structures import render_xyz_png_pymol

    try:
        index = sys.argv.index("--pymol-self-test")
        output = Path(sys.argv[index + 1]).resolve() if len(sys.argv) > index + 1 else Path.cwd() / "ChemAuto_PyMOL_Smoke.png"
        xyz = """4
ChemAuto PyMOL smoke test
C   0.000000   0.000000   0.000000
O   1.160000   0.000000   0.000000
H  -0.580000   0.920000   0.000000
H  -0.580000  -0.920000   0.000000
"""
        render_xyz_png_pymol(xyz, output)
        if not output.is_file() or output.stat().st_size < 512:
            raise RuntimeError(f"PyMOL did not create a valid PNG: {output}")
        print(f"PYMOL_SELF_TEST_OK: {output}")
        return 0
    except Exception as exc:
        print(f"PYMOL_SELF_TEST_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 31


if "--pymol-self-test" in sys.argv:
    raise SystemExit(_pymol_self_test())
elif "--gui" in sys.argv:
    from chemauto.gui.log_browser import main
else:
    from chemauto.cli import main

if __name__ == "__main__":
    main()
