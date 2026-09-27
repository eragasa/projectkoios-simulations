from __future__ import annotations

import unittest

from projectkoios.simulations.dft.pw.relaxation.base import (
    PwDftRelaxationScope,
)
from projectkoios.simulations.dft.pw.relaxation.capabilities import (
    PW_DFT_RELAXATION_BACKEND_DESCRIPTIONS,
    PW_DFT_RELAXATION_SCOPE_DESCRIPTIONS,
    PwDftRelaxationImplementationStatus,
    PwDftRelaxationInputModel,
)


class PwDftRelaxationBackendDescriptionTest(unittest.TestCase):
    def test_describes_every_generic_scope_once(self) -> None:
        self.assertEqual(
            {item.scope for item in PW_DFT_RELAXATION_SCOPE_DESCRIPTIONS},
            set(PwDftRelaxationScope),
        )
        self.assertEqual(
            len(PW_DFT_RELAXATION_SCOPE_DESCRIPTIONS),
            len(PwDftRelaxationScope),
        )

    def test_describes_each_backend_native_input_family(self) -> None:
        by_id = {
            item.integration_id.value: item
            for item in PW_DFT_RELAXATION_BACKEND_DESCRIPTIONS
        }

        self.assertEqual(set(by_id), {"quantum-espresso", "vasp", "abinit"})
        self.assertIs(
            by_id["quantum-espresso"].input_model,
            PwDftRelaxationInputModel.QE_PW_NAMELISTS_AND_CARDS,
        )
        self.assertIs(
            by_id["vasp"].input_model,
            PwDftRelaxationInputModel.VASP_NATIVE_FILES,
        )
        self.assertIs(
            by_id["abinit"].input_model,
            PwDftRelaxationInputModel.ABINIT_DATASETS_AND_VARIABLES,
        )
        self.assertIs(
            by_id["quantum-espresso"].status,
            PwDftRelaxationImplementationStatus.INPUT_PROJECTION_IMPLEMENTED,
        )
        self.assertIs(
            by_id["vasp"].status,
            PwDftRelaxationImplementationStatus.DESCRIBED_NOT_IMPLEMENTED,
        )
        self.assertIs(
            by_id["abinit"].status,
            PwDftRelaxationImplementationStatus.DESCRIBED_NOT_IMPLEMENTED,
        )


if __name__ == "__main__":
    unittest.main()
