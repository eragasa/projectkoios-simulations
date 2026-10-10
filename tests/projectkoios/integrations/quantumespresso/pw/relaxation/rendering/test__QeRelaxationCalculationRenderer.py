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
from projectkoios.simulations.structure import (
    StructureRecord,
    StructureRepresentation,
    StructureResolution,
    TransferredStructureProvenance,
)
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
        structure_path = path.parent / configuration.structure.repository_path
        unit_cell = UnitCellJsonCodec().loads(
            structure_path.read_text(encoding="utf-8"),
            expected_structure_id=configuration.structure.structure_id,
        )
        rendered = QeRelaxationCalculationRenderer().render(
            configuration,
            StructureResolution(
                record=StructureRecord(
                    structure_id=configuration.structure.structure_id,
                    representation=StructureRepresentation.primitive,
                    schema_version=1,
                    byte_size=configuration.structure.byte_size,
                    sha256=configuration.structure.sha256,
                    provenance=TransferredStructureProvenance(
                        source=structure_path.resolve().as_uri(),
                        revision=configuration.structure.sha256,
                        record_path=structure_path.name,
                        source_sha256=configuration.structure.sha256,
                        result_sha256=configuration.structure.sha256,
                    ),
                ),
                path=structure_path.resolve(),
                unit_cell=unit_cell,
            ),
        )

        self.assertEqual(
            hashlib.sha256(rendered.encode("ascii")).hexdigest(),
            "e30e5f549b2ac79f1b1b6d466dc623467043018b7b1990a8f16ef4c542f7d6c8",
        )
        self.assertNotIn("&CELL", rendered)

    def test_renders_the_declared_variable_cell_input_deterministically(self) -> None:
        path = _EXAMPLE_ROOT / "vc_relax/calculation.toml"
        configuration = QeRelaxationCalculationTomlLoader().load(path)
        structure_path = path.parent / configuration.structure.repository_path
        unit_cell = UnitCellJsonCodec().loads(
            structure_path.read_text(encoding="utf-8"),
            expected_structure_id=configuration.structure.structure_id,
        )
        rendered = QeRelaxationCalculationRenderer().render(
            configuration,
            StructureResolution(
                record=StructureRecord(
                    structure_id=configuration.structure.structure_id,
                    representation=StructureRepresentation.primitive,
                    schema_version=1,
                    byte_size=configuration.structure.byte_size,
                    sha256=configuration.structure.sha256,
                    provenance=TransferredStructureProvenance(
                        source=structure_path.resolve().as_uri(),
                        revision=configuration.structure.sha256,
                        record_path=structure_path.name,
                        source_sha256=configuration.structure.sha256,
                        result_sha256=configuration.structure.sha256,
                    ),
                ),
                path=structure_path.resolve(),
                unit_cell=unit_cell,
            ),
        )

        self.assertEqual(
            hashlib.sha256(rendered.encode("ascii")).hexdigest(),
            "7053bd423b8c002e37c08b89a8529439e0b727676981ee991b8680910974e611",
        )
        self.assertIn("&CELL", rendered)


if __name__ == "__main__":
    unittest.main()
