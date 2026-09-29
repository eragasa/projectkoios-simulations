from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pytest

from projectkoios.integrations.quantumespresso.pw.relaxation.loading import (  # noqa: E501
    QeRelaxationCalculationTomlLoader,
)
from projectkoios.integrations.quantumespresso.pw.relaxation.options import (
    QeIonicRelaxationOptions,
    QeLatticeVectorRelaxationOptions,
)
from tests.support.repository_root import REPOSITORY_ROOT

pytestmark = pytest.mark.integration

_EXAMPLE_ROOT = (
    REPOSITORY_ROOT / "examples/projectkoios/integrations/quantumespresso/"
    "pw/relaxation/Si/primitive"
)


class QeRelaxationCalculationTomlLoaderTest(unittest.TestCase):
    def test_loads_phase_specific_calculation_declarations(self) -> None:
        declarations = (
            (
                "relax/calculation.toml",
                "relax",
                "si-primitive-qe75-relax",
            ),
            (
                "vc_relax/calculation.toml",
                "vc-relax",
                "si-primitive-qe75-vc-relax",
            ),
        )

        for relative_path, phase, calculation_id in declarations:
            with self.subTest(relative_path=relative_path):
                configuration = QeRelaxationCalculationTomlLoader().load(
                    _EXAMPLE_ROOT / relative_path
                )

                self.assertEqual(configuration.phase, phase)
                self.assertEqual(configuration.calculation_id, calculation_id)
                self.assertEqual(configuration.integration_id, "quantum-espresso")
                self.assertEqual(
                    type(configuration.ionic_relaxation),
                    QeIonicRelaxationOptions,
                )
                expected_lattice_type = (
                    None if phase == "relax" else QeLatticeVectorRelaxationOptions
                )
                self.assertEqual(
                    None
                    if configuration.lattice_vector_relaxation is None
                    else type(configuration.lattice_vector_relaxation),
                    expected_lattice_type,
                )

    def test_rejects_unknown_schema_keys(self) -> None:
        content = (
            (_EXAMPLE_ROOT / "relax/calculation.toml")
            .read_text(encoding="utf-8")
            .replace(
                'integration_id = "quantum-espresso"',
                'integration_id = "quantum-espresso"\nundeclared_control = true',
            )
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "calculation.toml"
            path.write_text(content, encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "configuration schema mismatch"):
                QeRelaxationCalculationTomlLoader().load(path)

    def test_rejects_non_qe_integration(self) -> None:
        content = (
            (_EXAMPLE_ROOT / "relax/calculation.toml")
            .read_text(encoding="utf-8")
            .replace(
                'integration_id = "quantum-espresso"',
                'integration_id = "vasp"',
            )
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "calculation.toml"
            path.write_text(content, encoding="utf-8")

            with self.assertRaisesRegex(
                ValueError,
                "integration_id must be quantum-espresso",
            ):
                QeRelaxationCalculationTomlLoader().load(path)

    def test_rejects_lattice_options_for_fixed_cell_relaxation(self) -> None:
        content = (
            (_EXAMPLE_ROOT / "relax/calculation.toml").read_text(encoding="utf-8")
            + "\n[lattice_vector_relaxation]\n"
            + 'dynamics = "bfgs"\n'
            + 'degrees_of_freedom = "all"\n'
            + "target_pressure_kbar = 0.0\n"
            + "pressure_tolerance_kbar = 0.5\n"
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "calculation.toml"
            path.write_text(content, encoding="utf-8")

            with self.assertRaisesRegex(
                ValueError,
                "configuration schema mismatch",
            ):
                QeRelaxationCalculationTomlLoader().load(path)

    def test_rejects_a_symbolic_link(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            link = Path(temporary_directory) / "calculation.toml"
            link.symlink_to(_EXAMPLE_ROOT / "relax/calculation.toml")

            with self.assertRaisesRegex(
                ValueError,
                "configuration must be a bounded regular file",
            ):
                QeRelaxationCalculationTomlLoader().load(link)


if __name__ == "__main__":
    unittest.main()
