from __future__ import annotations

import unittest

from projectkoios.integrations.vasp.relaxation.data_extraction import (
    VaspRelaxDataExtractor,
)
from tests.projectkoios.integrations.vasp.nscf.data_extraction import (
    test__VaspNscfDataExtractor as nscf_test,
)


class VaspRelaxDataExtractorTest(unittest.TestCase):
    def test_retains_complete_source_ordered_ionic_trajectory(self) -> None:
        data = VaspRelaxDataExtractor().extract(nscf_test._sources())

        self.assertEqual(tuple(step.sequence_index for step in data.trajectory), (1,))
        self.assertEqual(len(data.trajectory[0].electronic_steps), 2)
        self.assertEqual(data.final_structure, data.trajectory[-1].structure)
        self.assertTrue(data.consistency.atom_count_matches)
        self.assertTrue(data.consistency.final_xml_structures_match)
        self.assertFalse(data.consistency.program_version_matches)
        self.assertFalse(data.consistency.kpoint_count_matches)
        self.assertFalse(data.consistency.final_energy_matches)


if __name__ == "__main__":
    unittest.main()
