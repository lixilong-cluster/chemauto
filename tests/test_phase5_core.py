from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from chemauto.core.gjf_document import GJFDocument
from chemauto.core.vde_ade_generator import generate_vde_ade_jobs
from chemauto.core.xyz_frames import parse_xyz_frames


MINIMAL_LOG = r'''
 #p ub3lyp/gen opt freq
 Charge = -1 Multiplicity = 4
 SCF Done:  E(UB3LYP) =  -100.000000000     A.U.
 Standard orientation:
 ---------------------------------------------------------------------
 Center     Atomic      Atomic             Coordinates (Angstroms)
 Number     Number       Type             X           Y           Z
 ---------------------------------------------------------------------
      1          6           0        0.000000    0.000000    0.000000
      2         26           0        1.800000    0.000000    0.000000
 ---------------------------------------------------------------------
 Optimization completed.
 Normal termination of Gaussian 16
'''


class Phase5CoreTests(unittest.TestCase):
    def test_multilink_gjf_roundtrip(self):
        text = (
            '%nprocshared=8\n%mem=8GB\n%chk=a.chk\n#p ub3lyp/def2tzvp opt=(calcfc,maxcycle=200) scf=xqc\n\n'
            'First\n\n-1 4\nC 0 0 0\nFe 1.8 0 0\n\n'
            '--Link1--\n%oldchk=a.chk\n%chk=a-stable.chk\n#p ub3lyp/chkbasis stable=opt geom=check guess=read\n\n'
            'Stable\n\n-1 4\n\n'
        )
        doc = GJFDocument.parse_text(text)
        self.assertEqual(len(doc.links), 2)
        self.assertEqual(doc.links[0].get_link0('nprocshared'), '8')
        self.assertIn('stable=opt', doc.links[1].components.build().lower())
        rendered = doc.render()
        self.assertIn('--Link1--', rendered)
        self.assertIn('%oldchk=a.chk', rendered)

    def test_no_chk_fallback_uses_log_coordinates_and_gen_tail(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); calc = root/'sample'; calc.mkdir()
            gjf = calc/'sample.gjf'; log = calc/'sample.log'
            gjf.write_text(
                '%nprocshared=8\n%mem=8GB\n%chk=sample.chk\n'
                '#p ub3lyp/gen opt freq scf=xqc\n\nTitle\n\n-1 4\n'
                'C 0 0 0\nFe 1.7 0 0\n\n'
                'C 0\n6-31G(d)\n****\nFe 0\nLANL2DZ\n****\n\n',
                encoding='utf-8'
            )
            log.write_text(MINIMAL_LOG, encoding='utf-8')
            jobs = generate_vde_ade_jobs(log, ('VDE', 'ADE'))
            self.assertEqual(len(jobs), 4)
            self.assertTrue(all(j.source_mode == 'coordinates' for j in jobs))
            for job in jobs:
                text = job.gjf.read_text(encoding='utf-8').lower()
                self.assertNotIn('%oldchk', text)
                self.assertNotIn('geom=check', text)
                self.assertNotIn('guess=read', text)
                self.assertNotIn('chkbasis', text)
                self.assertIn('ub3lyp/gen', text)
                self.assertIn('****', text)
                self.assertIn('fe', text)
                self.assertIsNone(job.copied_oldchk)

    def test_multiframe_xyz(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'traj.xyz'
            path.write_text(
                '2\nframe 1\nH 0 0 0\nH 0 0 0.7\n'
                '2\nframe 2\nH 0 0 0\nH 0 0 0.8\n', encoding='utf-8'
            )
            frames = parse_xyz_frames(path)
            self.assertEqual(len(frames), 2)
            self.assertIn('0.8', frames[1])


if __name__ == '__main__':
    unittest.main()
