from __future__ import annotations

import unittest

from projectkoios.integrations.vasp.outcar import VaspOutcarParser

OUTCAR = """
 vasp.5.3.5 31Mar14 complex
 NKPTS = 29 k-points in BZ
 NIONS = 2
 ENCUT = 400.0 eV
 -------------------------------- Iteration 1( 1) ----------------
 -------------------------------- Iteration 1( 2) ----------------
 aborting loop because EDIFF is reached
 free  energy   TOTEN  = -10.84056782 eV
 General timing and accounting informations for this job:
"""


class VaspOutcarParserTest(unittest.TestCase):
    def test_extracts_native_static_scf_observation(self) -> None:
        output = VaspOutcarParser().parse(OUTCAR)

        self.assertEqual(output.program_version, "5.3.5")
        self.assertEqual(output.atom_count, 2)
        self.assertEqual(output.irreducible_kpoint_count, 29)
        self.assertEqual(output.wavefunction_cutoff_ev, 400.0)
        self.assertEqual(output.electronic_iteration_count, 2)
        self.assertEqual(output.total_energy_toten_ev, -10.84056782)
        self.assertTrue(output.electronic_converged)
        self.assertTrue(output.completed)


if __name__ == "__main__":
    unittest.main()
