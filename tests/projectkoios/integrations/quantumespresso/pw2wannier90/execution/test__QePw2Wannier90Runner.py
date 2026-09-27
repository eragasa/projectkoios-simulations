from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from projectkoios.integrations.quantumespresso.pw2wannier90.configuration import (  # noqa: E501
    QePw2Wannier90InputConfiguration,
    QePw2Wannier90Mode,
    QePw2Wannier90SpinComponent,
)
from projectkoios.integrations.quantumespresso.pw2wannier90.execution import (  # noqa: E501
    QePw2Wannier90Runner,
    QePw2Wannier90RunRequest,
)
from projectkoios.integrations.quantumespresso.pw2wannier90.projection import (  # noqa: E501
    QePw2Wannier90InputProjector,
)


class QePw2Wannier90RunnerTest(unittest.TestCase):
    def test_render_only_requires_no_execution_resources(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "rendered"
            projection, _, _, _ = _resources(Path(directory))

            result = QePw2Wannier90Runner().run(
                QePw2Wannier90RunRequest(
                    projection=projection,
                    output_directory=output,
                )
            )

            self.assertFalse(result.execution_requested)
            self.assertTrue((output / "pw2wan.in").is_file())
            self.assertTrue(result.input_manifest.is_file())
            self.assertIsNone(result.artifact_manifest)

    def test_executes_after_staging_verified_nnkp_and_saved_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "run"
            projection, manifest_path, state_root, nnkp = _resources(root)
            executable = root / "pw2wannier90.x"
            executable.write_text(
                "#!/bin/sh\n"
                "printf 'amn\\n' > silicon.amn\n"
                "printf 'mmn\\n' > silicon.mmn\n"
                "printf 'eig\\n' > silicon.eig\n"
                "printf 'JOB DONE.\\n'\n",
                encoding="ascii",
            )
            executable.chmod(0o755)
            executable_payload = executable.read_bytes()

            result = QePw2Wannier90Runner().run(
                QePw2Wannier90RunRequest(
                    projection=projection,
                    output_directory=output,
                    execute=True,
                    executable=executable,
                    executable_sha256=hashlib.sha256(executable_payload).hexdigest(),
                    executable_byte_size=len(executable_payload),
                    nnkp_source=nnkp,
                    saved_state_manifest=manifest_path,
                    saved_state_source_root=state_root,
                    timeout_seconds=30.0,
                )
            )

            self.assertTrue(result.execution_requested)
            self.assertTrue((output / "tmp/system.save/wfc1.dat").is_file())
            self.assertTrue((output / "silicon.nnkp").is_file())
            self.assertTrue((output / "silicon.amn").is_file())
            artifact_manifest = json.loads(result.artifact_manifest.read_text())
            self.assertEqual(artifact_manifest["execution_status"], "succeeded")
            self.assertIn("silicon.eig", artifact_manifest["artifacts"])

    def test_identity_failure_precedes_output_directory_creation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "run"
            projection, manifest_path, state_root, nnkp = _resources(root)
            manifest_path.write_bytes(manifest_path.read_bytes() + b"\n")
            executable = root / "pw2wannier90.x"
            executable.write_text("#!/bin/sh\nexit 0\n", encoding="ascii")
            executable.chmod(0o755)
            executable_payload = executable.read_bytes()

            with self.assertRaisesRegex(ValueError, "manifest hash mismatch"):
                QePw2Wannier90Runner().run(
                    QePw2Wannier90RunRequest(
                        projection=projection,
                        output_directory=output,
                        execute=True,
                        executable=executable,
                        executable_sha256=hashlib.sha256(
                            executable_payload
                        ).hexdigest(),
                        executable_byte_size=len(executable_payload),
                        nnkp_source=nnkp,
                        saved_state_manifest=manifest_path,
                        saved_state_source_root=state_root,
                        timeout_seconds=30.0,
                    )
                )
            self.assertFalse(output.exists())


def _resources(
    root: Path,
) -> tuple[object, Path, Path, Path]:
    state_root = root / "state"
    save = state_root / "system.save"
    save.mkdir(parents=True)
    state_payloads = {
        "data-file-schema.xml": b"<qes/>\n",
        "charge-density.dat": b"charge\n",
        "wfc1.dat": b"wavefunction\n",
        "Si.UPF": b"pseudo\n",
    }
    for name, payload in state_payloads.items():
        (save / name).write_bytes(payload)
    artifacts = []
    for role, name in (
        ("qexsd", "data-file-schema.xml"),
        ("charge-density", "charge-density.dat"),
        ("wavefunction", "wfc1.dat"),
        ("pseudopotential", "Si.UPF"),
    ):
        payload = state_payloads[name]
        artifacts.append(
            {
                "role": role,
                "relative_path": f"system.save/{name}",
                "sha256": hashlib.sha256(payload).hexdigest(),
                "byte_size": len(payload),
            }
        )
    manifest_payload = json.dumps(
        {
            "schema_version": 1,
            "prefix": "system",
            "calculation": "nscf",
            "producer": {
                "program": "pw.x",
                "version": "7.5",
                "executable_sha256": "a" * 64,
            },
            "input_sha256": "b" * 64,
            "structure": {"structure_id": "Si.primitive", "sha256": "c" * 64},
            "pseudopotentials": [
                {
                    "symbol": "Si",
                    "filename": "Si.UPF",
                    "sha256": hashlib.sha256(state_payloads["Si.UPF"]).hexdigest(),
                    "byte_size": len(state_payloads["Si.UPF"]),
                }
            ],
            "artifacts": artifacts,
        },
        sort_keys=True,
    ).encode("utf-8")
    manifest_path = root / "saved-state-manifest.json"
    manifest_path.write_bytes(manifest_payload)
    nnkp = root / "silicon.nnkp"
    nnkp.write_bytes(b"nnkp\n")
    projection = QePw2Wannier90InputProjector().project(
        QePw2Wannier90InputConfiguration(
            prefix="system",
            outdir="./tmp/",
            seedname="silicon",
            spin_component=QePw2Wannier90SpinComponent.none,
            mode=QePw2Wannier90Mode.standalone,
            write_amn=True,
            write_mmn=True,
            write_unk=False,
            write_spn=False,
            input_filename="pw2wan.in",
            nnkp_filename="silicon.nnkp",
            nnkp_sha256=hashlib.sha256(nnkp.read_bytes()).hexdigest(),
            nnkp_byte_size=nnkp.stat().st_size,
            parent_nscf_saved_state_manifest_sha256=hashlib.sha256(
                manifest_payload
            ).hexdigest(),
        )
    )
    return projection, manifest_path, state_root, nnkp


if __name__ == "__main__":
    unittest.main()
