from __future__ import annotations

import unittest

from chemauto.core.gaussian_parser import LogSummary
from chemauto.core.record_sorting import energy_secondary_key, sort_records


class Phase6SortingTests(unittest.TestCase):
    def test_file_is_primary_and_energy_is_secondary(self):
        records = [
            LogSummary(path='a2.log', file='a.log', etot=-10.0),
            LogSummary(path='a1.log', file='a.log', etot=-11.0),
            LogSummary(path='b.log', file='b.log', etot=-20.0),
        ]
        result = sort_records(records, 'file')
        self.assertEqual([r.path for r in result], ['a1.log', 'a2.log', 'b.log'])

    def test_state_uses_multiplicity_then_energy(self):
        records = [
            LogSummary(path='m14b', file='m14b.log', state='14-A', multiplicity=14, etot=-9.0),
            LogSummary(path='m12', file='m12.log', state='12-A', multiplicity=12, etot=-8.0),
            LogSummary(path='m14a', file='m14a.log', state='14-B', multiplicity=14, etot=-10.0),
        ]
        result = sort_records(records, 'state')
        self.assertEqual([r.multiplicity for r in result], [12, 14, 14])
        self.assertEqual([r.path for r in result[1:]], ['m14a', 'm14b'])

    def test_etot_missing_falls_back_to_hf(self):
        records = [
            LogSummary(path='etot', file='etot.log', etot=-100.0, hf=-100.2),
            LogSummary(path='hf2', file='hf2.log', hf=-201.0),
            LogSummary(path='hf1', file='hf1.log', hf=-202.0),
            LogSummary(path='none', file='none.log'),
        ]
        result = sort_records(records, 'etot')
        self.assertEqual([r.path for r in result], ['hf1', 'hf2', 'etot', 'none'])

    def test_secondary_energy_uses_hf_when_etot_is_missing(self):
        etot = LogSummary(path='e', file='same.log', etot=-1.0, hf=-100.0)
        hf = LogSummary(path='h', file='same.log', hf=-200.0)
        self.assertLess(energy_secondary_key(hf), energy_secondary_key(etot))


if __name__ == '__main__':
    unittest.main()
