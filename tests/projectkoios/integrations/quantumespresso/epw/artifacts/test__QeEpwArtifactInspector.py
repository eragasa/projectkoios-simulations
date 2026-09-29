from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from projectkoios.integrations.quantumespresso.epw.artifacts import (
    QeEpwArtifactDeclaration,
    QeEpwArtifactInspector,
    QeEpwArtifactRole,
)


class QeEpwArtifactInspectorTest(unittest.TestCase):
    def test_verifies_declared_process_and_native_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            declarations = _artifacts(root)
            execution_sha256 = next(
                item.sha256
                for item in declarations
                if item.role is QeEpwArtifactRole.execution_record
            )

            observed = QeEpwArtifactInspector().inspect(
                output_directory=root,
                producer_execution_record_sha256=execution_sha256,
                declarations=declarations,
            )

            self.assertEqual(observed.artifact_count, 4)
            self.assertEqual(
                observed.total_byte_size,
                sum(item.byte_size for item in declarations),
            )

    def test_rejects_altered_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            declarations = _artifacts(root)
            (root / "linewidth.dat").write_bytes(b"altered\n")
            execution_sha256 = next(
                item.sha256
                for item in declarations
                if item.role is QeEpwArtifactRole.execution_record
            )

            with self.assertRaisesRegex(ValueError, "size mismatch"):
                QeEpwArtifactInspector().inspect(
                    output_directory=root,
                    producer_execution_record_sha256=execution_sha256,
                    declarations=declarations,
                )

    def test_rejects_symlinked_artifact_ancestors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            declarations = _artifacts(root)
            actual = root / "actual"
            actual.mkdir()
            payload = b"nested native output\n"
            (actual / "nested.dat").write_bytes(payload)
            (root / "linked").symlink_to(actual, target_is_directory=True)
            declarations += (
                QeEpwArtifactDeclaration(
                    role=QeEpwArtifactRole.native_output,
                    relative_path="linked/nested.dat",
                    sha256=hashlib.sha256(payload).hexdigest(),
                    byte_size=len(payload),
                ),
            )
            execution_sha256 = next(
                item.sha256
                for item in declarations
                if item.role is QeEpwArtifactRole.execution_record
            )

            with self.assertRaisesRegex(ValueError, "symlinked artifact path"):
                QeEpwArtifactInspector().inspect(
                    output_directory=root,
                    producer_execution_record_sha256=execution_sha256,
                    declarations=declarations,
                )

    def test_requires_canonical_process_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            declarations = tuple(
                item
                for item in _artifacts(root)
                if item.role is not QeEpwArtifactRole.stderr
            )
            execution_sha256 = next(
                item.sha256
                for item in declarations
                if item.role is QeEpwArtifactRole.execution_record
            )

            with self.assertRaisesRegex(ValueError, "canonical stderr"):
                QeEpwArtifactInspector().inspect(
                    output_directory=root,
                    producer_execution_record_sha256=execution_sha256,
                    declarations=declarations,
                )


def _artifacts(root: Path) -> tuple[QeEpwArtifactDeclaration, ...]:
    payloads = {
        "epw.out": b"Program EPW v.5.9 starts\n",
        "epw.err": b"",
        "execution.json": b'{"status":"succeeded"}\n',
        "linewidth.dat": b"native output\n",
    }
    roles = {
        "epw.out": QeEpwArtifactRole.stdout,
        "epw.err": QeEpwArtifactRole.stderr,
        "execution.json": QeEpwArtifactRole.execution_record,
        "linewidth.dat": QeEpwArtifactRole.native_output,
    }
    declarations = []
    for relative_path, payload in payloads.items():
        (root / relative_path).write_bytes(payload)
        declarations.append(
            QeEpwArtifactDeclaration(
                role=roles[relative_path],
                relative_path=relative_path,
                sha256=hashlib.sha256(payload).hexdigest(),
                byte_size=len(payload),
            )
        )
    return tuple(declarations)


if __name__ == "__main__":
    unittest.main()
