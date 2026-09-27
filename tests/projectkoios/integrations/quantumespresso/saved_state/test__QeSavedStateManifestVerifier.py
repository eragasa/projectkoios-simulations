from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from projectkoios.integrations.quantumespresso.saved_state import (
    QeSavedStateManifestJsonCodec,
    QeSavedStateManifestVerifier,
)


class QeSavedStateManifestVerifierTest(unittest.TestCase):
    def test_loads_closed_manifest_and_verifies_selected_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_payload = _write_saved_state(root)

            manifest = QeSavedStateManifestJsonCodec().loads(manifest_payload)
            paths = QeSavedStateManifestVerifier().verify(manifest, root)

            self.assertEqual(
                tuple(path.relative_to(root).as_posix() for path in paths),
                (
                    "system.save/data-file-schema.xml",
                    "system.save/charge-density.dat",
                    "system.save/wfc1.dat",
                    "system.save/Si.UPF",
                ),
            )
            self.assertEqual(manifest.producer_version, "7.5")

    def test_rejects_unexpected_manifest_key(self) -> None:
        document = json.loads(_manifest_payload(_artifacts()))
        document["machine_local_path"] = "/tmp/run"

        with self.assertRaisesRegex(ValueError, "unexpected"):
            QeSavedStateManifestJsonCodec().loads(json.dumps(document).encode("utf-8"))

    def test_rejects_tampered_selected_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = QeSavedStateManifestJsonCodec().loads(_write_saved_state(root))
            (root / "system.save" / "wfc1.dat").write_bytes(b"tampered")

            with self.assertRaisesRegex(ValueError, "size mismatch"):
                QeSavedStateManifestVerifier().verify(manifest, root)

    def test_rejects_symbolic_link(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = _write_saved_state(root)
            wavefunction = root / "system.save" / "wfc1.dat"
            target = root / "target"
            target.write_bytes(wavefunction.read_bytes())
            wavefunction.unlink()
            wavefunction.symlink_to(target)

            with self.assertRaisesRegex(ValueError, "not a regular file"):
                QeSavedStateManifestVerifier().verify(
                    QeSavedStateManifestJsonCodec().loads(payload),
                    root,
                )


def _write_saved_state(root: Path) -> bytes:
    save = root / "system.save"
    save.mkdir()
    payloads = {
        "data-file-schema.xml": b"<qes/>\n",
        "charge-density.dat": b"charge\n",
        "wfc1.dat": b"wavefunction\n",
        "Si.UPF": b"pseudo\n",
    }
    for name, payload in payloads.items():
        (save / name).write_bytes(payload)
    return _manifest_payload(
        (
            _artifact("qexsd", "data-file-schema.xml", payloads),
            _artifact("charge-density", "charge-density.dat", payloads),
            _artifact("wavefunction", "wfc1.dat", payloads),
            _artifact("pseudopotential", "Si.UPF", payloads),
        )
    )


def _artifacts() -> tuple[dict[str, object], ...]:
    payloads = {
        "data-file-schema.xml": b"<qes/>\n",
        "charge-density.dat": b"charge\n",
        "wfc1.dat": b"wavefunction\n",
        "Si.UPF": b"pseudo\n",
    }
    return (
        _artifact("qexsd", "data-file-schema.xml", payloads),
        _artifact("charge-density", "charge-density.dat", payloads),
        _artifact("wavefunction", "wfc1.dat", payloads),
        _artifact("pseudopotential", "Si.UPF", payloads),
    )


def _artifact(
    role: str,
    name: str,
    payloads: dict[str, bytes],
) -> dict[str, object]:
    payload = payloads[name]
    return {
        "role": role,
        "relative_path": f"system.save/{name}",
        "sha256": hashlib.sha256(payload).hexdigest(),
        "byte_size": len(payload),
    }


def _manifest_payload(artifacts: tuple[dict[str, object], ...]) -> bytes:
    return json.dumps(
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
                    "sha256": hashlib.sha256(b"pseudo\n").hexdigest(),
                    "byte_size": len(b"pseudo\n"),
                }
            ],
            "artifacts": artifacts,
        },
        sort_keys=True,
    ).encode("utf-8")


if __name__ == "__main__":
    unittest.main()
