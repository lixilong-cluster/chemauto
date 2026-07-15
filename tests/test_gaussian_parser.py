from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from chemauto.core.gaussian_parser import (
    delta_e_ev,
    minimum_etot,
    parse_gaussian_log,
)


class GaussianParserRegressionTests(unittest.TestCase):
    DATA = Path(__file__).resolve().parents[1] / "test_data" / "logs"

    def test_real_wrapped_archive_fields(self):
        expected = {
            "fe3c2-2A.log": ("Cs", "10-A'", -3866.59761359),
            "fe3c3-3A.log": ("C1", "10-A", -3904.65452777),
            "fe3c4-4A.log": ("C2v", "10-B1", -3942.72807187),
            "fe3c5-5A.log": ("Cs", "10-A'", -3980.77441658),
            "fe3c6-6A.log": ("Cs", "10-A'", -4018.85781476),
            "fe3c7-7A.log": ("C1", "4-A", -4056.87848959),
            "fe3c7-7B.log": ("C1", "8-A", -4056.91800568),
            "fe3c8-8A.log": ("C2h", "10-BU", -4094.97304192),
        }
        for name, (sym, state, hf) in expected.items():
            with self.subTest(name=name):
                result = parse_gaussian_log(self.DATA / name)
                self.assertEqual(result.sym, sym)
                self.assertEqual(result.state, state)
                self.assertAlmostEqual(result.hf, hf, places=10)
                self.assertIsNone(result.nimag)  # These are NBO SP jobs, not freq jobs.
                self.assertIsNone(result.freq_completed)
                self.assertTrue(result.normal_termination)

    def test_opt_freq_and_stable_opt_step_selection(self):
        synthetic = """
 ------------------------------
 #p opt freq ub3lyp/6-31g(d)
 ------------------------------
 Charge = -1 Multiplicity = 2
 SCF Done:  E(UB3LYP) =  -100.000000000     A.U.
 SCF Done:  E(UB3LYP) =  -100.100000000     A.U.
 Optimization completed.
 ------------------------------
 #P Geom=AllCheck Guess=TCheck GenChk Freq
 ------------------------------
 Charge = -1 Multiplicity = 2
 SCF Done:  E(UB3LYP) =  -100.100000000     A.U.
 Harmonic frequencies
 Frequencies --   -12.0  100.0  200.0
 Zero-point correction= 0.050000 (Hartree/Particle)
 Sum of electronic and zero-point Energies= -100.050000
 1\\1\\GINC-X\\Freq\\UB3LYP\\6-31G(d)\\X\\-1,2\\State=2-A\\HF=-100.100000\\PG=C01\\NImag=1\\@
 Normal termination
 ------------------------------
 #p stable=opt geom=allcheck guess=read chkbasis
 ------------------------------
 Charge = -1 Multiplicity = 2
 The wavefunction has an internal instability.
 SCF Done:  E(UB3LYP) =  -100.120000000     A.U.
 The wavefunction is stable under the perturbations considered.
 Normal termination
 """
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "synthetic.log"
            path.write_text(synthetic, encoding="utf-8")
            result = parse_gaussian_log(path)
        self.assertAlmostEqual(result.hf, -100.1, places=10)
        self.assertAlmostEqual(result.zpe, 0.05, places=10)
        self.assertAlmostEqual(result.etot, -100.05, places=10)
        self.assertEqual(result.state, "2-A")
        self.assertEqual(result.sym, "C1")
        self.assertEqual(result.nimag, 1)
        self.assertTrue(result.freq_completed)
        self.assertEqual(result.stable_1, "unstable")
        self.assertEqual(result.stable_2, "stable")
        self.assertEqual(result.scf_energies, [-100.0, -100.1])

    def test_delta_e_zero_does_not_depend_on_list_order(self):
        a = parse_gaussian_log(self.DATA / "fe3c2-2A.log")
        b = parse_gaussian_log(self.DATA / "fe3c3-3A.log")
        # Inject Etot values because these test data are SP/NBO calculations.
        a.etot = -10.0
        b.etot = -9.9
        base1 = minimum_etot([a, b])
        base2 = minimum_etot([b, a])
        self.assertEqual(base1, base2)
        self.assertAlmostEqual(delta_e_ev(a, base1), 0.0, places=12)
        self.assertGreater(delta_e_ev(b, base1), 0.0)


if __name__ == "__main__":
    unittest.main()
