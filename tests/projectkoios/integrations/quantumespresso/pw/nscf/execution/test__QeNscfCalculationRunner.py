from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from projectkoios.integrations.quantumespresso.pw.inputfile.model import ControlBlock
from projectkoios.integrations.quantumespresso.pw.nscf.artifacts import (
    QeNscfArtifactInspector,
)
from projectkoios.integrations.quantumespresso.pw.nscf.cards import (
    QeNscfControlBlock,
)
from projectkoios.integrations.quantumespresso.pw.nscf.execution import (
    QeNscfCalculationRunner,
    QeNscfCalculationRunRequest,
)
from projectkoios.integrations.quantumespresso.pw.nscf.loading import (
    QeNscfCalculationTomlLoader,
)
from projectkoios.integrations.quantumespresso.pw2wannier90.configuration import (
    QePw2Wannier90InputConfiguration,
    QePw2Wannier90Mode,
    QePw2Wannier90SpinComponent,
)
from projectkoios.integrations.quantumespresso.pw2wannier90.execution import (
    QePw2Wannier90Runner,
    QePw2Wannier90RunRequest,
)
from projectkoios.integrations.quantumespresso.pw2wannier90.projection import (
    QePw2Wannier90InputProjector,
)
from projectkoios.integrations.quantumespresso.saved_state import (
    QeSavedStateCalculation,
    QeSavedStateManifestBuilder,
    QeSavedStateManifestJsonCodec,
    QeSavedStatePseudopotential,
)
from tests.support.repository_root import REPOSITORY_ROOT


class QeNscfCalculationRunnerTest(unittest.TestCase):
    def test_loader_extracts_complete_grid_and_control_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            resources = _resources(Path(directory))
            configuration = QeNscfCalculationTomlLoader().load(resources.configuration)
            projection = configuration.projection_configuration()

            self.assertEqual(len(projection.kpoints), 64)
            self.assertEqual(projection.kpoints[0].coordinates, (0.0, 0.0, 0.0))
            self.assertEqual(projection.kpoints[1].coordinates, (0.0, 0.0, 0.25))
            self.assertEqual(projection.kpoints[-1].coordinates, (0.75, 0.75, 0.75))
            self.assertAlmostEqual(sum(item.weight for item in projection.kpoints), 1.0)
            self.assertTrue(issubclass(QeNscfControlBlock, ControlBlock))

    def test_configuration_cannot_declare_execution_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            resources = _resources(Path(directory))
            resources.configuration.write_text(
                "execute = true\n" + resources.configuration.read_text()
            )

            with self.assertRaisesRegex(ValueError, "extra=\\['execute'\\]"):
                QeNscfCalculationTomlLoader().load(resources.configuration)

    def test_render_only_uses_configuration_paths_without_execution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            resources = _resources(Path(directory))

            result = QeNscfCalculationRunner().run(
                QeNscfCalculationRunRequest(
                    configuration_path=resources.configuration,
                )
            )

            self.assertFalse(result.execution_requested)
            self.assertTrue((result.output_directory / "pw.in").is_file())
            text = (result.output_directory / "pw.in").read_text()
            self.assertIn("verbosity = 'high'", text)
            self.assertIn("diagonalization = 'cg'", text)
            self.assertIn("K_POINTS crystal\n 64", text)
            self.assertFalse((result.output_directory / "execution.json").exists())

    def test_executes_stub_and_produces_verified_nscf_saved_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            resources = _resources(Path(directory))

            result = QeNscfCalculationRunner().run(
                QeNscfCalculationRunRequest(
                    configuration_path=resources.configuration,
                    execute=True,
                    timeout_seconds=30.0,
                )
            )

            self.assertTrue(result.execution_requested)
            assert result.saved_state_manifest is not None
            manifest = QeSavedStateManifestJsonCodec().loads(
                result.saved_state_manifest.read_bytes()
            )
            self.assertIs(manifest.calculation, QeSavedStateCalculation.nscf)
            self.assertEqual(manifest.prefix, "si")
            self.assertTrue(
                (result.output_directory / "tmp/si.save/wfc1.dat").is_file()
            )
            assert result.artifact_manifest is not None
            artifact_manifest = json.loads(result.artifact_manifest.read_text())
            self.assertEqual(artifact_manifest["execution_status"], "succeeded")
            assert result.saved_state_handoff is not None
            artifacts = QeNscfArtifactInspector().inspect(
                output_directory=result.output_directory,
                input_filename="pw.in",
                saved_state_manifest=result.saved_state_handoff.manifest_path,
                saved_state_source_root=result.saved_state_handoff.source_root,
            )
            self.assertEqual(artifacts.prefix, "si")
            self.assertEqual(artifacts.qexsd_file.path.name, "data-file-schema.xml")

    def test_hands_verified_nscf_state_to_pw2wannier90_runner(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            resources = _resources(root)
            nscf_result = QeNscfCalculationRunner().run(
                QeNscfCalculationRunRequest(
                    configuration_path=resources.configuration,
                    execute=True,
                    timeout_seconds=30.0,
                )
            )
            assert nscf_result.saved_state_handoff is not None
            handoff = nscf_result.saved_state_handoff
            nnkp = root / "silicon.nnkp"
            nnkp.write_bytes(b"nnkp\n")
            converter = root / "pw2wannier90.x"
            converter.write_text(
                "#!/bin/sh\n"
                "test -f tmp/si.save/data-file-schema.xml || exit 8\n"
                "printf 'amn\\n' > silicon.amn\n"
                "printf 'mmn\\n' > silicon.mmn\n"
                "printf 'eig\\n' > silicon.eig\n"
                "printf 'JOB DONE.\\n'\n",
                encoding="ascii",
            )
            converter.chmod(0o755)
            projection = QePw2Wannier90InputProjector().project(
                QePw2Wannier90InputConfiguration(
                    prefix=handoff.prefix,
                    outdir="./tmp/",
                    seedname="silicon",
                    spin_component=QePw2Wannier90SpinComponent.none,
                    mode=QePw2Wannier90Mode.standalone,
                    write_amn=True,
                    write_mmn=True,
                    write_unk=False,
                    write_spn=False,
                    input_filename="pw2wan.in",
                    nnkp_filename=nnkp.name,
                    nnkp_sha256=_sha256(nnkp),
                    nnkp_byte_size=nnkp.stat().st_size,
                    parent_nscf_saved_state_manifest_sha256=(handoff.manifest_sha256),
                )
            )

            result = QePw2Wannier90Runner().run(
                QePw2Wannier90RunRequest(
                    projection=projection,
                    output_directory=root / "pw2-run",
                    execute=True,
                    executable=converter,
                    executable_sha256=_sha256(converter),
                    executable_byte_size=converter.stat().st_size,
                    nnkp_source=nnkp,
                    saved_state_manifest=handoff.manifest_path,
                    saved_state_source_root=handoff.source_root,
                    timeout_seconds=30.0,
                )
            )

            self.assertTrue(result.execution_requested)
            self.assertTrue((result.output_directory / "silicon.amn").is_file())
            self.assertTrue(
                (result.output_directory / "tmp/si.save/wfc1.dat").is_file()
            )

    def test_parent_identity_failure_precedes_output_creation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            resources = _resources(Path(directory))
            configuration = resources.configuration.read_text()
            resources.configuration.write_text(
                configuration.replace(resources.parent_manifest_sha256, "0" * 64)
            )

            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                QeNscfCalculationRunner().run(
                    QeNscfCalculationRunRequest(
                        configuration_path=resources.configuration,
                        execute=True,
                        timeout_seconds=30.0,
                    )
                )

            self.assertFalse(resources.output.exists())


class _Resources:
    def __init__(
        self,
        *,
        configuration: Path,
        output: Path,
        parent_manifest_sha256: str,
    ) -> None:
        self.configuration = configuration
        self.output = output
        self.parent_manifest_sha256 = parent_manifest_sha256


def _resources(root: Path) -> _Resources:
    source_input = root / "silicon.nscf"
    source_input.write_bytes(b"source NSCF input\n")
    structure = root / "Si.primitive.json"
    shutil.copyfile(
        REPOSITORY_ROOT
        / "examples/projectkoios/integrations/quantumespresso/pw/relaxation/"
        "Si/primitive/Si.primitive.json",
        structure,
    )
    pseudopotential = root / "Si.pbe-n-van.UPF"
    pseudopotential.write_bytes(b"pseudo\n")
    executable = root / "pw.x"
    executable.write_text(
        "#!/bin/sh\n"
        "test -f tmp/si.save/data-file-schema.xml || exit 7\n"
        "printf '<qes nscf=\"true\"/>\\n' > tmp/si.save/data-file-schema.xml\n"
        "printf 'Program PWSCF v.7.5\\nJOB DONE.\\n'\n",
        encoding="ascii",
    )
    executable.chmod(0o755)

    parent_output = root / "parent"
    parent_state = parent_output / "state"
    save = parent_state / "si.save"
    save.mkdir(parents=True)
    state_payloads = {
        "data-file-schema.xml": b'<qes scf="true"/>\n',
        "charge-density.dat": b"charge\n",
        "wfc1.dat": b"wavefunction\n",
        "Si.pbe-n-van.UPF": pseudopotential.read_bytes(),
    }
    for name, payload in state_payloads.items():
        (save / name).write_bytes(payload)
    pseudo_identity = QeSavedStatePseudopotential(
        symbol="Si",
        filename=pseudopotential.name,
        sha256=_sha256(pseudopotential),
        byte_size=pseudopotential.stat().st_size,
    )
    parent_manifest = QeSavedStateManifestBuilder().build(
        source_root=parent_state,
        prefix="si",
        calculation=QeSavedStateCalculation.scf,
        producer_version="7.5",
        executable_sha256=_sha256(executable),
        input_sha256="1" * 64,
        structure_id="Si.primitive",
        structure_sha256=_sha256(structure),
        pseudopotentials=(pseudo_identity,),
    )
    parent_manifest_path = parent_output / "scf-saved-state-manifest.json"
    parent_manifest_path.write_bytes(
        QeSavedStateManifestJsonCodec().dumps(parent_manifest)
    )
    output = root / "nscf-run"
    configuration = root / "calculation.toml"
    configuration.write_text(
        _configuration_text(
            source_input=source_input,
            structure=structure,
            executable=executable,
            pseudopotential=pseudopotential,
            parent_output=parent_output,
            parent_state=parent_state,
            parent_manifest=parent_manifest_path,
            output=output,
        ),
        encoding="utf-8",
    )
    return _Resources(
        configuration=configuration,
        output=output,
        parent_manifest_sha256=_sha256(parent_manifest_path),
    )


def _configuration_text(
    *,
    source_input: Path,
    structure: Path,
    executable: Path,
    pseudopotential: Path,
    parent_output: Path,
    parent_state: Path,
    parent_manifest: Path,
    output: Path,
) -> str:
    def resource(path: Path) -> str:
        return (
            f"path = {json.dumps(str(path))}\n"
            f"byte_size = {path.stat().st_size}\n"
            f'sha256 = "{_sha256(path)}"\n'
        )

    return (
        "schema_version = 1\n"
        'calculation_id = "si-primitive-wannier-nscf"\n'
        'phase = "nscf"\n'
        'integration_id = "quantum-espresso"\n\n'
        "[source_input]\n"
        + resource(source_input)
        + "\n[structure]\n"
        + resource(structure)
        + 'structure_id = "Si.primitive"\n\n'
        + "[calculator]\n"
        + resource(executable)
        + 'program = "pw.x"\nprogram_version = "7.5"\n\n'
        + "[parent_scf]\n"
        + f"output_directory = {json.dumps(str(parent_output))}\n"
        + f"saved_state_root = {json.dumps(str(parent_state))}\n"
        + f"manifest_path = {json.dumps(str(parent_manifest))}\n"
        + f"manifest_byte_size = {parent_manifest.stat().st_size}\n"
        + f'manifest_sha256 = "{_sha256(parent_manifest)}"\n'
        + 'calculation = "scf"\nprefix = "si"\n\n'
        + "[pseudopotential]\n"
        + resource(pseudopotential)
        + 'symbol = "Si"\nfilename = "Si.pbe-n-van.UPF"\nmass_amu = 28.0\n\n'
        + "[sampling]\n"
        + "kpoint_grid = [4, 4, 4]\nkpoint_offset = [0, 0, 0]\n"
        + "band_count = 12\nwavefunction_cutoff_ry = 25.0\n"
        + 'electronic_tolerance_ry = 1.0e-12\noccupations = "fixed"\n\n'
        + "[qe]\n"
        + 'prefix = "si"\npseudo_dir = "./"\noutdir = "./tmp/"\n'
        + 'input_filename = "pw.in"\nverbosity = "high"\niprint = 2\n'
        + 'diagonalization = "cg"\ndiago_full_acc = true\n'
        + "disable_symmetry = true\ndisable_time_reversal = true\n"
        + "coordinate_precision = 8\nkpoint_precision = 12\n\n"
        + "[output]\n"
        + f"directory = {json.dumps(str(output))}\n\n"
        + "[qualification]\n"
        + 'statements = ["Software fixture only; no scientific validation."]\n'
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    unittest.main()
