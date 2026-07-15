from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FreshBuildIntegrityTests(unittest.TestCase):
    def test_complete_build_entry_and_pymol_runtime_are_present(self):
        required = [
            ROOT / "build_cli.py",
            ROOT / "ChemAuto_Portable.spec",
            ROOT / "src" / "pymol" / "_cmd.cp311-win_amd64.pyd",
            ROOT / "src" / "pymol" / "VCOMP140.DLL",
            ROOT / "src" / "pymol" / "pymol_path" / "LICENSE",
        ]
        missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
        self.assertEqual([], missing)

    def test_suite_launcher_knows_reference_explorer_subfolder(self):
        text = (ROOT / "src" / "chemauto" / "core" / "reference_search_launcher.py").read_text(encoding="utf-8")
        self.assertIn('exe_dir / "ReferenceExplorer" / "ReferenceExplorer.exe"', text)

    def test_reference_explorer_uses_bundled_playwright_browser(self):
        text = (ROOT / "tools" / "reference_explorer" / "ReferenceExplorer.py").read_text(encoding="utf-8")
        self.assertIn("PLAYWRIGHT_BROWSERS_PATH", text)
        self.assertIn('"pw-browsers"', text)


if __name__ == "__main__":
    unittest.main()
