from __future__ import annotations

import unittest

from projectkoios.simulations.dft.pw.settings import (
    CalculationType,
    PwDftSettings,
)


class PwDftSettingsTest(unittest.TestCase):
    def test_retains_the_calculation_type_selected_once(self) -> None:
        settings = PwDftSettings(calculation_type=CalculationType.vc_relax)

        self.assertIs(settings.calculation_type, CalculationType.vc_relax)

    def test_rejects_an_untyped_calculation_string(self) -> None:
        with self.assertRaisesRegex(TypeError, "must be a CalculationType"):
            PwDftSettings(calculation_type="scf")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
