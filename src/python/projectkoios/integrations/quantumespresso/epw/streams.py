"""Parse bounded native ``epw.x`` captured streams."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

_MAX_STREAM_BYTES = 64 * 1024 * 1024
_VERSION = re.compile(r"Program\s+EPW\s+v\.?\s*([^\s(]+)", re.IGNORECASE)
_FATAL_MARKERS = (
    "Error in routine",
    "%%%%%%%%%%%%",
    "SIGSEGV",
    "MPI_ABORT",
    "stopping ...",
)


@dataclass(frozen=True, slots=True)
class QeEpwStreamObservation:
    """Retain stream identities and provider-native execution observations."""

    stdout_sha256: str
    stdout_byte_size: int
    stderr_sha256: str
    stderr_byte_size: int
    program_version: str | None
    job_done: bool
    total_program_execution_reported: bool
    wannierization_reported: bool
    electron_phonon_interpolation_reported: bool
    fatal_diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class QeEpwStreamParser:
    """Observe native diagnostics without imposing scientific acceptance policy."""

    def parse(
        self,
        stdout_payload: bytes,
        stderr_payload: bytes,
    ) -> QeEpwStreamObservation:
        """Decode bounded streams and retain exact identities and native markers."""
        stdout = _decode(stdout_payload, "stdout")
        stderr = _decode(stderr_payload, "stderr")
        combined = f"{stdout}\n{stderr}"
        version_match = _VERSION.search(stdout)
        fatal_diagnostics = tuple(
            line.strip()
            for line in combined.splitlines()
            if any(marker.casefold() in line.casefold() for marker in _FATAL_MARKERS)
        )
        return QeEpwStreamObservation(
            stdout_sha256=hashlib.sha256(stdout_payload).hexdigest(),
            stdout_byte_size=len(stdout_payload),
            stderr_sha256=hashlib.sha256(stderr_payload).hexdigest(),
            stderr_byte_size=len(stderr_payload),
            program_version=(version_match.group(1) if version_match else None),
            job_done="JOB DONE." in stdout,
            total_program_execution_reported=(
                "Total program execution" in stdout
                and re.search(r"^\s*EPW\s*:", stdout, re.MULTILINE) is not None
            ),
            wannierization_reported=(
                "Wannierization on" in stdout or "Running Wannier90" in stdout
            ),
            electron_phonon_interpolation_reported=(
                "Electron-Phonon interpolation" in stdout
            ),
            fatal_diagnostics=fatal_diagnostics,
        )


def _decode(payload: bytes, label: str) -> str:
    if type(payload) is not bytes:
        raise TypeError(f"{label} payload must be bytes")
    if len(payload) > _MAX_STREAM_BYTES:
        raise ValueError(f"{label} exceeds the byte limit")
    return payload.decode("utf-8", errors="replace")
