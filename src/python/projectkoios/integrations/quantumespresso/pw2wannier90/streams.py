"""Parse bounded native ``pw2wannier90.x`` captured streams."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

_MAX_STREAM_BYTES = 8 * 1024 * 1024
_VERSION = re.compile(r"Program\s+PW2WANNIER\s+v\.([^\s]+)\s+starts", re.IGNORECASE)
_WANNIER_COUNT = re.compile(r"Number of wannier functions is ok\s*\(\s*(\d+)\)")
_FATAL_MARKERS = ("Error in routine", "%%%%%%%%%%%%", "SIGSEGV", "MPI_ABORT")


@dataclass(frozen=True, slots=True)
class QePw2Wannier90StreamObservation:
    """Retain exact stream identities and native completion observations."""

    stdout_sha256: str
    stdout_byte_size: int
    stderr_sha256: str
    stderr_byte_size: int
    program_version: str | None
    job_done: bool
    real_lattice_accepted: bool
    reciprocal_lattice_accepted: bool
    kpoints_accepted: bool
    wannier_function_count: int | None
    guiding_functions_complete: bool
    all_neighbors_found: bool
    amn_calculated: bool
    mmn_calculated: bool
    fatal_diagnostics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class QePw2Wannier90StreamParser:
    """Parse native diagnostics without making workflow-acceptance decisions."""

    def parse(
        self,
        stdout_payload: bytes,
        stderr_payload: bytes,
    ) -> QePw2Wannier90StreamObservation:
        """Decode bounded ASCII-compatible streams and retain native facts."""
        stdout = _decode(stdout_payload, "stdout")
        stderr = _decode(stderr_payload, "stderr")
        combined = f"{stdout}\n{stderr}"
        version_match = _VERSION.search(stdout)
        wannier_match = _WANNIER_COUNT.search(stdout)
        fatal_diagnostics = tuple(
            line.strip()
            for line in combined.splitlines()
            if any(marker.casefold() in line.casefold() for marker in _FATAL_MARKERS)
        )
        return QePw2Wannier90StreamObservation(
            stdout_sha256=hashlib.sha256(stdout_payload).hexdigest(),
            stdout_byte_size=len(stdout_payload),
            stderr_sha256=hashlib.sha256(stderr_payload).hexdigest(),
            stderr_byte_size=len(stderr_payload),
            program_version=(version_match.group(1) if version_match else None),
            job_done="JOB DONE." in stdout,
            real_lattice_accepted="- Real lattice is ok" in stdout,
            reciprocal_lattice_accepted="- Reciprocal lattice is ok" in stdout,
            kpoints_accepted="- K-points are ok" in stdout,
            wannier_function_count=(
                int(wannier_match.group(1)) if wannier_match else None
            ),
            guiding_functions_complete=("- All guiding functions are given" in stdout),
            all_neighbors_found="All neighbours are found" in stdout,
            amn_calculated="AMN calculated" in stdout,
            mmn_calculated="MMN calculated" in stdout,
            fatal_diagnostics=fatal_diagnostics,
        )


def _decode(payload: bytes, label: str) -> str:
    if type(payload) is not bytes:
        raise TypeError(f"{label} payload must be bytes")
    if len(payload) > _MAX_STREAM_BYTES:
        raise ValueError(f"{label} exceeds the byte limit")
    return payload.decode("utf-8", errors="replace")
