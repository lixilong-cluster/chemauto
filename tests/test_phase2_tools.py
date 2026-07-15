from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from chemauto.core.related_files import resolve_related_files
from chemauto.core.gjf_stability import ChemAutoGJFHandler, read_text_safely
from chemauto.core.fchk_xyz import convert_one
from chemauto.core.remote_formchk import RemoteFormchkProfile


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "test_data" / "tools"


class Phase2ToolTests(unittest.TestCase):
    def test_exact_related_file_resolution(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            for name in ("sample.log", "sample.gjf", "sample.chk", "sample.fchk", "sample-check.chk", "sample-stable.chk", "sample2.chk"):
                (d / name).write_text("x", encoding="utf-8")
            r = resolve_related_files(d / "sample.log")
            self.assertEqual(r.gjf.name, "sample.gjf")
            self.assertEqual(r.chk.name, "sample.chk")
            self.assertEqual(r.fchk.name, "sample.fchk")
            self.assertEqual(r.check_chk.name, "sample-check.chk")
            self.assertNotIn("sample2.chk", [p.name for p in r.existing().values()])

    def test_verified_stable_check_checkpoint_paths(self):
        text = "%nprocshared=8\n%mem=8GB\n%chk=fe4c6-a029014.chk\n#p upbepbe/def2tzvp opt freq int=superfine\n\nTitle\n\n-1 14\nFe 0 0 0\nC 0 0 2\n\n"
        h = ChemAutoGJFHandler(); h.load_from_text(text, filename="fe4c6-a029014")
        ok, msg = h.add_stability_check("stable")
        self.assertTrue(ok, msg)
        out = h.build_text().lower()
        self.assertIn("%oldchk=fe4c6-a029014.chk", out)
        self.assertIn("%chk=fe4c6-a029014-check.chk", out)
        self.assertIn("stable", out)

    def test_verified_stable_opt_checkpoint_paths(self):
        text = "%nprocshared=8\n%mem=8GB\n%chk=fe4c6-a029014.chk\n#p upbepbe/def2tzvp opt freq int=superfine\n\nTitle\n\n-1 14\nFe 0 0 0\nC 0 0 2\n\n"
        h = ChemAutoGJFHandler(); h.load_from_text(text, filename="fe4c6-a029014")
        ok, msg = h.add_stability_check("stable=opt")
        self.assertTrue(ok, msg)
        out = h.build_text().lower()
        self.assertIn("%oldchk=fe4c6-a029014.chk", out)
        self.assertIn("%chk=fe4c6-a029014-stable.chk", out)
        self.assertIn("stable=opt", out)

    def test_gen_basis_stability_uses_chkbasis(self):
        text = "%chk=genjob.chk\n#p ubpw91/gen opt freq int=superfine\n\nTitle\n\n-1 5\nFe 0 0 0\nC 0 0 2\n\nFe 0\nSDD\n****\nC 0\n6-311+G(d)\n****\n\n"
        h = ChemAutoGJFHandler(); h.load_from_text(text, filename="genjob")
        ok, msg = h.add_stability_check("stable")
        self.assertTrue(ok, msg)
        out = h.build_text().lower()
        self.assertIn("chkbasis", out)
        self.assertIn("%oldchk=genjob.chk", out)

    def test_genecp_stable_opt_uses_chkbasis(self):
        text = "%chk=ecpjob.chk\n#p upbepbe/genecp opt\n\nTitle\n\n-1 3\nSb 0 0 0\nC 0 0 2\n\nSb 0\nSDD\n****\nC 0\ndef2TZVP\n****\n\nSb 0\nSDD\n\n"
        h = ChemAutoGJFHandler(); h.load_from_text(text, filename="ecpjob")
        ok, msg = h.add_stability_check("stable=opt")
        self.assertTrue(ok, msg)
        out = h.build_text().lower()
        self.assertIn("chkbasis", out)
        self.assertIn("%chk=ecpjob-stable.chk", out)

    def test_fchk_to_xyz_real_file(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            fixture = td / "sample.fchk"
            fixture.write_text(
                "Atomic numbers                          I   N=           2\n"
                "           6           1\n"
                "Current cartesian coordinates           R   N=           6\n"
                " 0.000000000000E+00 0.000000000000E+00 0.000000000000E+00\n"
                " 0.000000000000E+00 0.000000000000E+00 2.000000000000E+00\n",
                encoding="utf-8",
            )
            out = convert_one(fixture, out_dir=td, overwrite=False)
            lines = out.read_text(encoding="utf-8").splitlines()
            self.assertEqual(int(lines[0]), 2)
            self.assertEqual(len(lines), 4)

    def test_remote_profile_has_no_password_field(self):
        data = RemoteFormchkProfile(name="x", remote_user="u", remote_host="h", remote_exec_node="node", remote_command="c")
        encoded = json.dumps(data.__dict__).lower()
        self.assertNotIn("password", encoded)


if __name__ == "__main__":
    unittest.main()
