from __future__ import annotations

import dataclasses
import unittest

from projectkoios.integrations.quantumespresso.pw.inputfile.model import (
    ControlBlock,
)
from projectkoios.simulations.dft.pw.settings import CalculationType


class ControlBlockTest(unittest.TestCase):
    def test_retains_typed_calculation(self) -> None:
        block = ControlBlock(calculation_type=CalculationType.scf)

        self.assertIs(block.calculation_type, CalculationType.scf)

    def test_is_immutable(self) -> None:
        block = ControlBlock(calculation_type=CalculationType.bands)

        with self.assertRaises(dataclasses.FrozenInstanceError):
            block.calculation_type = CalculationType.scf  # type: ignore[misc]

    def test_rejects_an_untyped_string(self) -> None:
        with self.assertRaisesRegex(TypeError, "must be a CalculationType"):
            ControlBlock(calculation_type="scf")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
