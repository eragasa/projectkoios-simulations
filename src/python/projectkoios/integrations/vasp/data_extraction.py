"""Common retained-artifact extraction for VASP calculation modes."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path

from projectkoios.integrations.vasp.data import (
    VaspDataSources,
    VaspExecutionData,
    VaspNativeArtifact,
)
from projectkoios.integrations.vasp.outcar import VaspOutcarParser
from projectkoios.integrations.vasp.run_xml import VaspRunXmlParser


class VaspDataArtifactError(ValueError):
    """Report invalid, escaped, oversized, or failed retained VASP evidence."""


@dataclass(frozen=True, slots=True)
class VaspDataSourceExtractor:
    """Extract exact common VASP sources without mode-specific interpretation."""

    artifact_root: Path
    maximum_artifact_bytes: int = 100_000_000
    maximum_identity_artifact_bytes: int = 20_000_000_000

    def __post_init__(self) -> None:
        if not self.artifact_root.is_dir() or self.artifact_root.is_symlink():
            raise ValueError("artifact_root must be an existing nonsymlink directory")
        if type(self.maximum_artifact_bytes) is not int or (
            self.maximum_artifact_bytes <= 0
        ):
            raise ValueError("maximum_artifact_bytes must be positive")
        if type(self.maximum_identity_artifact_bytes) is not int or (
            self.maximum_identity_artifact_bytes <= 0
        ):
            raise ValueError("maximum_identity_artifact_bytes must be positive")

    def extract(self, output_artifact_id: str) -> VaspDataSources:
        """Extract OUTCAR, execution evidence, and optional sibling artifacts."""
        outcar_path = self._resolve(output_artifact_id)
        run_directory = outcar_path.parent
        execution_path = run_directory / "execution.json"
        execution_payload = self._read(execution_path)
        execution = _execution(execution_payload)
        self._reject_captured_failure(run_directory, execution)
        outcar_payload = self._read(outcar_path)
        outcar = VaspOutcarParser().parse(outcar_payload.decode("utf-8"))
        artifacts = [
            self._artifact("outcar", outcar_path, outcar_payload),
            self._artifact("execution", execution_path, execution_payload),
        ]
        vasprun = None
        for role, filename in (
            ("vasprun", "vasprun.xml"),
            ("oszicar", "OSZICAR"),
            ("contcar", "CONTCAR"),
        ):
            path = run_directory / filename
            if not path.is_file() or path.is_symlink():
                continue
            payload = self._read(path)
            artifacts.append(self._artifact(role, path, payload))
            if role == "vasprun" and payload:
                vasprun = VaspRunXmlParser(
                    maximum_bytes=self.maximum_artifact_bytes
                ).parse(payload)
        for role, filename in (
            ("wavecar", "WAVECAR"),
            ("chgcar", "CHGCAR"),
            ("locpot", "LOCPOT"),
            ("procar", "PROCAR"),
        ):
            path = run_directory / filename
            if path.is_file() and not path.is_symlink():
                artifacts.append(self._identity_artifact(role, path))
        for role, captured_filename in (
            ("stdout", execution.stdout_filename),
            ("stderr", execution.stderr_filename),
        ):
            if captured_filename is None:
                continue
            path = run_directory / captured_filename
            payload = self._read(path)
            artifacts.append(self._artifact(role, path, payload))
        return VaspDataSources(
            execution=execution,
            artifacts=tuple(artifacts),
            outcar=outcar,
            vasprun=vasprun,
        )

    def _reject_captured_failure(
        self,
        run_directory: Path,
        execution: VaspExecutionData,
    ) -> None:
        if execution.stdout_filename is None:
            return
        payload = self._read(run_directory / execution.stdout_filename)
        if b"triple product of the basis vectors is negative" in payload:
            raise VaspDataArtifactError(
                "VASP rejected the POSCAR because its lattice basis is left-handed"
            )

    def _resolve(self, artifact_id: str) -> Path:
        if not artifact_id or Path(artifact_id).is_absolute():
            raise VaspDataArtifactError("artifact_id must be a relative path")
        root = self.artifact_root.resolve()
        path = (root / artifact_id).resolve()
        if not path.is_relative_to(root):
            raise VaspDataArtifactError("artifact_id must remain inside artifact_root")
        if not path.is_file() or path.is_symlink():
            raise FileNotFoundError(path)
        return path

    def _read(self, path: Path) -> bytes:
        if not path.is_file() or path.is_symlink():
            raise FileNotFoundError(path)
        if path.stat().st_size > self.maximum_artifact_bytes:
            raise VaspDataArtifactError(f"artifact exceeds byte limit: {path}")
        payload = path.read_bytes()
        if len(payload) > self.maximum_artifact_bytes:
            raise VaspDataArtifactError(f"artifact exceeds byte limit: {path}")
        return payload

    def _artifact(
        self,
        role: str,
        path: Path,
        payload: bytes,
    ) -> VaspNativeArtifact:
        return VaspNativeArtifact(
            role=role,
            relative_path=str(path.relative_to(self.artifact_root.resolve())),
            sha256=hashlib.sha256(payload).hexdigest(),
            byte_size=len(payload),
        )

    def _identity_artifact(self, role: str, path: Path) -> VaspNativeArtifact:
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode):
            raise VaspDataArtifactError(f"identity artifact is not regular: {path}")
        if before.st_size > self.maximum_identity_artifact_bytes:
            raise VaspDataArtifactError(f"identity artifact exceeds byte limit: {path}")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        digest = hashlib.sha256()
        byte_count = 0
        try:
            opened_before = os.fstat(descriptor)
            if not stat.S_ISREG(opened_before.st_mode) or _identity(opened_before) != (
                _identity(before)
            ):
                raise VaspDataArtifactError(
                    f"identity artifact changed before hashing: {path}"
                )
            with os.fdopen(descriptor, "rb", closefd=False) as stream:
                while chunk := stream.read(1024 * 1024):
                    byte_count += len(chunk)
                    if byte_count > self.maximum_identity_artifact_bytes:
                        raise VaspDataArtifactError(
                            f"identity artifact exceeds byte limit: {path}"
                        )
                    digest.update(chunk)
            opened_after = os.fstat(descriptor)
        finally:
            os.close(descriptor)
        after = path.lstat()
        if (
            byte_count != opened_before.st_size
            or _fingerprint(opened_before) != _fingerprint(opened_after)
            or _fingerprint(opened_after) != _fingerprint(after)
        ):
            raise VaspDataArtifactError(
                f"identity artifact changed while hashing: {path}"
            )
        return VaspNativeArtifact(
            role=role,
            relative_path=str(path.relative_to(self.artifact_root.resolve())),
            sha256=digest.hexdigest(),
            byte_size=byte_count,
        )


def _identity(value: os.stat_result) -> tuple[int, int]:
    return value.st_dev, value.st_ino


def _fingerprint(value: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _execution(payload: bytes) -> VaspExecutionData:
    parsed = json.loads(payload.decode("utf-8"))
    if not isinstance(parsed, dict) or parsed.get("schema_version") != 1:
        raise VaspDataArtifactError("unsupported execution record")
    if (
        parsed.get("status") != "succeeded"
        or type(parsed.get("returncode")) is not int
        or parsed.get("returncode") != 0
    ):
        raise VaspDataArtifactError("VASP execution record is not successful")
    stdout = parsed.get("stdout_filename")
    stderr = parsed.get("stderr_filename")
    if stdout is not None and not isinstance(stdout, str):
        raise VaspDataArtifactError("stdout_filename must be a string")
    if stderr is not None and not isinstance(stderr, str):
        raise VaspDataArtifactError("stderr_filename must be a string")
    return VaspExecutionData(
        status="succeeded",
        returncode=0,
        stdout_filename=stdout,
        stderr_filename=stderr,
    )
