"""Common immutable source records for VASP calculation data facades."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath

from projectkoios.integrations.vasp.outcar import VaspOutcar
from projectkoios.integrations.vasp.run_xml import VaspRunXmlData

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True, slots=True)
class VaspNativeArtifact:
    """Identify one exact native VASP artifact after it is complete."""

    role: str
    relative_path: str
    sha256: str
    byte_size: int

    def __post_init__(self) -> None:
        if (
            type(self.role) is not str
            or not self.role
            or self.role != self.role.strip()
        ):
            raise ValueError("role must be a nonempty stripped string")
        if type(self.relative_path) is not str or not self.relative_path:
            raise ValueError("relative_path must be nonempty")
        path = PurePosixPath(self.relative_path)
        if (
            "\\" in self.relative_path
            or path.is_absolute()
            or path == PurePosixPath(".")
            or ".." in path.parts
        ):
            raise ValueError("relative_path must be a safe relative POSIX path")
        if type(self.sha256) is not str or _SHA256.fullmatch(self.sha256) is None:
            raise ValueError("sha256 must be lowercase SHA-256")
        if type(self.byte_size) is not int or self.byte_size < 0:
            raise ValueError("byte_size must be nonnegative")


@dataclass(frozen=True, slots=True)
class VaspExecutionData:
    """Retain terminal execution evidence used by VASP extraction."""

    status: str
    returncode: int
    stdout_filename: str | None
    stderr_filename: str | None

    def __post_init__(self) -> None:
        if self.status != "succeeded":
            raise ValueError("VASP execution status must be succeeded")
        if type(self.returncode) is not int or self.returncode != 0:
            raise ValueError("VASP execution returncode must be zero")
        for label, value in (
            ("stdout_filename", self.stdout_filename),
            ("stderr_filename", self.stderr_filename),
        ):
            if value is not None and (
                type(value) is not str
                or not value
                or value in {".", ".."}
                or "/" in value
                or "\\" in value
            ):
                raise ValueError(f"{label} must be a basename or None")


@dataclass(frozen=True, slots=True)
class VaspDataSources:
    """Compose exact VASP artifacts with parsed OUTCAR and XML observations."""

    execution: VaspExecutionData
    artifacts: tuple[VaspNativeArtifact, ...]
    outcar: VaspOutcar
    vasprun: VaspRunXmlData | None = None

    def __post_init__(self) -> None:
        if type(self.execution) is not VaspExecutionData:
            raise TypeError("execution must be VaspExecutionData")
        if type(self.artifacts) is not tuple or not self.artifacts:
            raise ValueError("artifacts must be a nonempty tuple")
        if any(type(item) is not VaspNativeArtifact for item in self.artifacts):
            raise TypeError("artifacts must contain VaspNativeArtifact values")
        roles = tuple(item.role for item in self.artifacts)
        paths = tuple(item.relative_path for item in self.artifacts)
        if len(set(roles)) != len(roles):
            raise ValueError("artifact roles must be unique")
        if len(set(paths)) != len(paths):
            raise ValueError("artifact paths must be unique")
        if "outcar" not in roles or "execution" not in roles:
            raise ValueError("artifacts must include outcar and execution")
        if type(self.outcar) is not VaspOutcar:
            raise TypeError("outcar must be VaspOutcar")
        if self.vasprun is not None and type(self.vasprun) is not VaspRunXmlData:
            raise TypeError("vasprun must be VaspRunXmlData or None")
        if self.vasprun is not None and "vasprun" not in roles:
            raise ValueError("parsed vasprun data requires a vasprun artifact")

    def artifact(self, role: str) -> VaspNativeArtifact | None:
        """Return the artifact for one unique role when retained."""
        return next((item for item in self.artifacts if item.role == role), None)
