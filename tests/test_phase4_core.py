from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from chemauto.core.dos_pairs import identify_dos_pairs
from chemauto.core.external_open import can_open_related
from chemauto.core.gaussian_parser import LogSummary, grouped_delta_e_ev, minimum_etot_by_group
from chemauto.core.vde_ade_generator import generate_vde_ade_jobs
from chemauto.infra.config import DEFAULT_USER_CONFIG


class Phase4CoreTests(unittest.TestCase):
    def test_delta_e_uses_one_global_zero_without_automatic_grouping(self):
        a = LogSummary(path='a.log', file='a.log', cluster='C3Fe4', charge=-1, etot=-100.0)
        b = LogSummary(path='b.log', file='b.log', cluster='C3Fe4', charge=-1, etot=-99.9)
        c = LogSummary(path='c.log', file='c.log', cluster='C7Fe4', charge=0, etot=-200.0)
        bases = minimum_etot_by_group([a, b, c])
        self.assertGreater(grouped_delta_e_ev(a, bases), 0.0)
        self.assertGreater(grouped_delta_e_ev(b, bases), grouped_delta_e_ev(a, bases))
        self.assertAlmostEqual(grouped_delta_e_ev(c, bases), 0.0)
        self.assertEqual(len(bases), 1)

    def test_selected_dos_files_do_not_cross_pair_directories(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); a = root/'a'; b = root/'b'; a.mkdir(); b.mkdir()
            curve = a/'same_curve.txt'; line = b/'same_line.txt'
            curve.write_text('', encoding='utf-8'); line.write_text('', encoding='utf-8')
            pairs = identify_dos_pairs([curve, line])
            self.assertEqual(len(pairs), 2)
            self.assertTrue(all(not pair.complete for pair in pairs))

    def test_vde_ade_input_generator_preserves_verified_names(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); calc = root/'calc'; calc.mkdir()
            gjf = calc/'sample.gjf'; chk = calc/'sample.chk'; chk.write_bytes(b'checkpoint')
            gjf.write_text(
                '%nprocshared=8\n%mem=8GB\n%chk=sample.chk\n#p upbepbe/gen opt freq scf=xqc\n\nTitle\n\n-1 10\nFe 0 0 0\n\nFe 0\nGEN BASIS\n\n',
                encoding='utf-8'
            )
            jobs = generate_vde_ade_jobs(gjf, ('VDE', 'ADE'))
            self.assertEqual(len(jobs), 4)
            names = {job.directory.name for job in jobs}
            self.assertEqual(names, {'sample-VDE-M9', 'sample-VDE-M11', 'sample-ADE-M9', 'sample-ADE-M11'})
            for job in jobs:
                text = job.gjf.read_text(encoding='utf-8')
                self.assertIn('chkbasis', text.lower())
                self.assertIn('geom=check', text.lower())
                self.assertTrue(job.copied_oldchk.exists())

    def test_chk_is_never_opened_directly(self):
        self.assertFalse(can_open_related('sample.chk'))
        self.assertTrue(can_open_related('sample.fchk'))

    def test_default_photon_energy_is_355_nm(self):
        self.assertAlmostEqual(float(DEFAULT_USER_CONFIG['default_photon_energy']), 3.493, places=6)


if __name__ == '__main__':
    unittest.main()
