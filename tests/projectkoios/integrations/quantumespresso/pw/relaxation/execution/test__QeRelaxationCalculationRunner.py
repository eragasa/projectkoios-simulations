from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import pytest

from projectkoios.integrations.quantumespresso.pw.relaxation.execution import (  # noqa: E501
    QeRelaxationCalculationRunner,
    QeRelaxationCalculationRunRequest,
    QeRelaxationStructureOverride,
)
from projectkoios.integrations.quantumespresso.pw.relaxation.loading import (  # noqa: E501
    QeRelaxationCalculationTomlLoader,
)
from tests.support.repository_root import REPOSITORY_ROOT

pytestmark = pytest.mark.integration

_EXAMPLE_ROOT = (
    REPOSITORY_ROOT / "examples/projectkoios/integrations/quantumespresso/"
    "pw/relaxation/Si/primitive"
)
_CONFIGURATION = _EXAMPLE_ROOT / "relax/calculation.toml"
_STRUCTURE = _EXAMPLE_ROOT / "Si.primitive.json"
_EXPECTED_INPUT_SHA256 = (
    "f4990b1a4152c61d3d7ad7887b13543c0afa58e7470d82da27f066d1ea3b7b40"
)


class QeRelaxationCalculationRunnerTest(unittest.TestCase):
    def test_render_only_writes_a_configuration_bound_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "rendered"

            result = QeRelaxationCalculationRunner().run(
                QeRelaxationCalculationRunRequest(
                    configuration_path=_CONFIGURATION,
                    output_directory=output,
                )
            )

            self.assertFalse(result.execution_requested)
            self.assertIsNone(result.artifact_manifest)
            self.assertEqual(
                {path.name for path in output.iterdir()},
                {"input-manifest.json", "pw.in"},
            )
            manifest = json.loads(result.input_manifest.read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema_version"], 1)
            self.assertEqual(manifest["calculation_id"], "si-primitive-qe75-relax")
            self.assertEqual(
                manifest["configuration_sha256"],
                hashlib.sha256(_CONFIGURATION.read_bytes()).hexdigest(),
            )
            self.assertEqual(manifest["input"]["sha256"], _EXPECTED_INPUT_SHA256)

    def test_committed_vc_relax_manifest_matches_its_static_fixture(self) -> None:
        configuration_path = _EXAMPLE_ROOT / "vc_relax/calculation.toml"
        manifest = json.loads(
            (_EXAMPLE_ROOT / "vc_relax/input/input-manifest.json").read_text(
                encoding="utf-8"
            )
        )
        configuration = QeRelaxationCalculationTomlLoader().load(configuration_path)

        self.assertEqual(
            manifest["configuration_sha256"],
            hashlib.sha256(configuration_path.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            manifest["qualification"], list(configuration.qualification_statements)
        )
        self.assertEqual(
            manifest["input"]["sha256"],
            hashlib.sha256(
                (_EXAMPLE_ROOT / "vc_relax/input/pw.in").read_bytes()
            ).hexdigest(),
        )

    def test_configuration_symlink_is_not_resolved_around_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            configuration_link = root / "calculation.toml"
            configuration_link.symlink_to(_CONFIGURATION)
            output = root / "must-not-exist"

            with self.assertRaisesRegex(
                ValueError,
                "configuration must be a bounded regular file",
            ):
                QeRelaxationCalculationRunner().run(
                    QeRelaxationCalculationRunRequest(
                        configuration_path=configuration_link,
                        output_directory=output,
                    )
                )

            self.assertFalse(output.exists())

    def test_structure_hash_failure_precedes_output_creation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "must-not-exist"
            request = QeRelaxationCalculationRunRequest(
                configuration_path=_CONFIGURATION,
                output_directory=output,
                structure_override=QeRelaxationStructureOverride(
                    path=_STRUCTURE,
                    structure_id="Si.primitive",
                    sha256="0" * 64,
                ),
            )

            with self.assertRaisesRegex(ValueError, "structure SHA-256 mismatch"):
                QeRelaxationCalculationRunner().run(request)

            self.assertFalse(output.exists())

    def test_execution_resource_failure_precedes_output_creation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            executable = root / "pw.x"
            pseudopotential = root / "Si.UPF"
            executable.write_bytes(b"not the declared executable")
            pseudopotential.write_bytes(b"not the declared pseudopotential")
            output = root / "must-not-exist"
            request = QeRelaxationCalculationRunRequest(
                configuration_path=_CONFIGURATION,
                output_directory=output,
                execute=True,
                executable=executable,
                pseudopotential=pseudopotential,
            )

            with self.assertRaisesRegex(ValueError, "calculator byte-size mismatch"):
                QeRelaxationCalculationRunner().run(request)

            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
