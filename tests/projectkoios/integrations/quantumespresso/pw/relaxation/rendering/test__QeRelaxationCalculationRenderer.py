from __future__ import annotations

import hashlib
import unittest

import pytest

from projectkoios.integrations.quantumespresso.pw.relaxation.loading import (  # noqa: E501
    QeRelaxationCalculationTomlLoader,
)
from projectkoios.integrations.quantumespresso.pw.relaxation.rendering import (  # noqa: E501
    QeRelaxationCalculationRenderer,
)
from projectkoios.physkit.periodic.unit_cell import UnitCellJsonCodec
from tests.support.repository_root import REPOSITORY_ROOT

pytestmark = pytest.mark.integration

_EXAMPLE_ROOT = (
    REPOSITORY_ROOT / "examples/projectkoios/integrations/quantumespresso/"
    "pw/relaxation/Si/primitive"
)


class QeRelaxationCalculationRendererTest(unittest.TestCase):
    def test_renders_the_declared_fixed_cell_input_deterministically(self) -> None:
        path = _EXAMPLE_ROOT / "relax/calculation.toml"
        configuration = QeRelaxationCalculationTomlLoader().load(path)
        unit_cell = UnitCellJsonCodec().loads(
            (path.parent / configuration.structure.repository_path).read_text(
                encoding="utf-8"
            ),
            expected_structure_id=configuration.structure.structure_id,
        )

        rendered = QeRelaxationCalculationRenderer().render(
            configuration,
            unit_cell,
        )

        self.assertEqual(
            hashlib.sha256(rendered.encode("ascii")).hexdigest(),
            "f4990b1a4152c61d3d7ad7887b13543c0afa58e7470d82da27f066d1ea3b7b40",
        )
        self.assertNotIn("&CELL", rendered)

    def test_renders_the_declared_variable_cell_input_deterministically(self) -> None:
        path = _EXAMPLE_ROOT / "vc_relax/calculation.toml"
        configuration = QeRelaxationCalculationTomlLoader().load(path)
        unit_cell = UnitCellJsonCodec().loads(
            (path.parent / configuration.structure.repository_path).read_text(
                encoding="utf-8"
            ),
            expected_structure_id=configuration.structure.structure_id,
        )

        rendered = QeRelaxationCalculationRenderer().render(configuration, unit_cell)

        self.assertEqual(
            hashlib.sha256(rendered.encode("ascii")).hexdigest(),
            "c7ecb8d346113c4f73dcc4226bf7e9275f225113f1e6c0b0083f328e16674e06",
        )
        self.assertIn("&CELL", rendered)


if __name__ == "__main__":
    unittest.main()
