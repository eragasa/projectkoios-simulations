"""Stream relaxation stdout to storage and the trajectory parser independently."""

from __future__ import annotations

import codecs
import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO, Literal

from projectkoios.integrations.quantumespresso.outputs.base import (
    QuantumEspressoOutputFileError,
)
from projectkoios.integrations.quantumespresso.outputs.pw_stderr import (
    QePwStderrFile,
    QePwStderrFileParser,
)
from projectkoios.integrations.quantumespresso.outputs.pw_stdout import (
    QePwStdoutFile,
    QePwStdoutFileParser,
    QePwStdoutFileResult,
)
from projectkoios.integrations.quantumespresso.pw.data_extraction.base import (
    QePwCapturedStreamData,
    QePwNativeArtifact,
)
from projectkoios.integrations.quantumespresso.pw.relaxation.trajectory import (
    QeRelaxationTrajectory,
    QeRelaxationTrajectoryParser,
)

_MAX_RETAINED_BYTES = 100_000_000
_RETAINED_LINE = re.compile(
    r"(?:"
    r"Program\s+PWSCF\s+v\."
    r"|number of atoms/cell\s*="
    r"|number of k points\s*="
    r"|kinetic-energy cutoff\s*="
    r"|!\s+total energy\s*="
    r"|convergence (?:has been achieved|NOT achieved)"
    r"|Forces acting on atoms"
    r"|atom\s+\d+\s+type\s+\d+\s+force\s*="
    r"|Total force\s*="
    r"|total\s+stress\s+\(Ry/bohr\*\*3\)"
    r"|\bP=\s*"
    r"|number of scf cycles\s*="
    r"|number of bfgs steps\s*="
    r"|bfgs converged in"
    r"|criteria:\s*energy\s*<"
    r"|End of BFGS Geometry Optimization"
    r"|Final\s+(?:energy|enthalpy)\s*="
    r"|axis vectors are left-handed"
    r"|^\s*iteration\s+#"
    r"|JOB DONE\."
    r"|\b(?:energy|enthalpy)\s+(?:old|new)\s*="
    r"|CELL_PARAMETERS"
    r"|ATOMIC_POSITIONS"
    r"|Begin final coordinates"
    r"|End final coordinates"
    r")",
    re.I,
)
_STRESS_HEADER = re.compile(r"total\s+stress\s+\(Ry/bohr\*\*3\)", re.I)
_CELL_HEADER = re.compile(r"^\s*CELL_PARAMETERS", re.I)
_POSITIONS_HEADER = re.compile(r"^\s*ATOMIC_POSITIONS", re.I)


@dataclass(slots=True)
class QeRelaxationTrajectoryStreamParser:
    """Retain only trajectory-bearing lines while stdout arrives in chunks."""

    calculation: Literal["relax", "vc-relax"]
    _decoder: codecs.IncrementalDecoder = field(init=False, repr=False)
    _pending_text: str = field(default="", init=False, repr=False)
    _retained: bytearray = field(default_factory=bytearray, init=False, repr=False)
    _fixed_rows_remaining: int = field(default=0, init=False, repr=False)
    _positions_active: bool = field(default=False, init=False, repr=False)
    _finished: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.calculation not in {"relax", "vc-relax"}:
            raise ValueError("calculation must be relax or vc-relax")
        self._decoder = codecs.getincrementaldecoder("utf-8")(errors="strict")

    def feed(self, chunk: bytes) -> None:
        """Consume one nonempty stdout chunk without retaining unrelated text."""
        if self._finished:
            raise RuntimeError("trajectory stream parser is already finished")
        if type(chunk) is not bytes:
            raise TypeError("stdout chunk must be bytes")
        if not chunk:
            return
        self._pending_text += self._decoder.decode(chunk, final=False)
        lines = self._pending_text.split("\n")
        self._pending_text = lines.pop()
        for line in lines:
            self._consume_line(line.removesuffix("\r"))

    def finish(
        self,
        *,
        summary: QePwStdoutFileResult | None = None,
        output_file: QePwStdoutFile | None = None,
    ) -> QeRelaxationTrajectory:
        """Finalize decoding and parse the compact trajectory projection once."""
        if self._finished:
            raise RuntimeError("trajectory stream parser is already finished")
        if summary is not None and type(summary) is not QePwStdoutFileResult:
            raise TypeError("summary must be a QePwStdoutFileResult or None")
        if output_file is not None and type(output_file) is not QePwStdoutFile:
            raise TypeError("output_file must be a QePwStdoutFile or None")
        if summary is None and output_file is None:
            raise ValueError("output_file is required when summary is omitted")
        self._pending_text += self._decoder.decode(b"", final=True)
        if self._pending_text:
            self._consume_line(self._pending_text.removesuffix("\r"))
        self._pending_text = ""
        self._finished = True
        retained = bytes(self._retained)
        if summary is None:
            assert output_file is not None
            summary = QePwStdoutFileParser().parse(
                retained,
                output_file=output_file,
            )
        return QeRelaxationTrajectoryParser().parse(
            retained,
            calculation=self.calculation,
            summary=summary,
        )

    @property
    def retained_byte_count(self) -> int:
        """Report compact parser input retained independently of full stdout."""
        return len(self._retained)

    def _consume_line(self, line: str) -> None:
        if self._fixed_rows_remaining > 0:
            self._retain(line)
            self._fixed_rows_remaining -= 1
            return
        if self._positions_active:
            values = line.split()
            if len(values) in {4, 7}:
                self._retain(line)
                return
            self._positions_active = False
        if not _RETAINED_LINE.search(line):
            return
        self._retain(line)
        if _STRESS_HEADER.search(line) or _CELL_HEADER.search(line):
            self._fixed_rows_remaining = 3
        elif _POSITIONS_HEADER.search(line):
            self._positions_active = True

    def _retain(self, line: str) -> None:
        encoded = f"{line}\n".encode()
        if len(self._retained) + len(encoded) > _MAX_RETAINED_BYTES:
            raise QuantumEspressoOutputFileError(
                "retained relaxation trajectory exceeds the byte limit"
            )
        self._retained.extend(encoded)


@dataclass(frozen=True, slots=True)
class QeRelaxationStdoutTee:
    """Copy stdout once while feeding the independent trajectory parser."""

    chunk_size: int = 1024 * 1024

    def __post_init__(self) -> None:
        if type(self.chunk_size) is not int or self.chunk_size <= 0:
            raise ValueError("chunk_size must be a positive integer")

    def copy(
        self,
        source: BinaryIO,
        destination: BinaryIO,
        parser: QeRelaxationTrajectoryStreamParser,
    ) -> int:
        """Write every source byte before exposing its chunk to the parser."""
        if type(parser) is not QeRelaxationTrajectoryStreamParser:
            raise TypeError("parser must be QeRelaxationTrajectoryStreamParser")
        byte_count = 0
        while True:
            chunk = source.read(self.chunk_size)
            if not chunk:
                break
            if type(chunk) is not bytes:
                raise TypeError("binary stdout source must return bytes")
            _write_all(destination, chunk)
            parser.feed(chunk)
            byte_count += len(chunk)
        destination.flush()
        return byte_count


def extract_streamed_relaxation_sources(
    *,
    calculation: Literal["relax", "vc-relax"],
    stdout_source: BinaryIO,
    stdout_destination: Path,
    stderr_payload: bytes,
    stdout_relative_path: str = "pw.out",
    stderr_relative_path: str = "pw.err",
) -> tuple[QePwCapturedStreamData, QeRelaxationTrajectory]:
    """Tee stdout once, parse a compact projection, then identify stored bytes."""
    if not isinstance(stdout_destination, Path):
        raise TypeError("stdout_destination must be a Path")
    if not stdout_destination.parent.is_dir() or stdout_destination.parent.is_symlink():
        raise ValueError("stdout destination parent must be a nonsymlink directory")
    if stdout_destination.exists() or stdout_destination.is_symlink():
        raise ValueError("stdout destination must not already exist")
    if type(stderr_payload) is not bytes:
        raise TypeError("stderr_payload must be bytes")
    parser = QeRelaxationTrajectoryStreamParser(calculation=calculation)
    with stdout_destination.open("xb") as destination:
        byte_count = QeRelaxationStdoutTee().copy(
            stdout_source,
            destination,
            parser,
        )
    stdout_file = QePwStdoutFile(relative_path=stdout_relative_path)
    trajectory = parser.finish(output_file=stdout_file)
    stdout_artifact = QePwNativeArtifact(
        relative_path=stdout_relative_path,
        sha256=_sha256_file(stdout_destination),
        byte_size=byte_count,
    )
    stderr_artifact = QePwNativeArtifact(
        relative_path=stderr_relative_path,
        sha256=hashlib.sha256(stderr_payload).hexdigest(),
        byte_size=len(stderr_payload),
    )
    stderr = QePwStderrFileParser().parse(
        stderr_payload,
        output_file=QePwStderrFile(relative_path=stderr_relative_path),
    )
    return (
        QePwCapturedStreamData(
            stdout_artifact=stdout_artifact,
            stderr_artifact=stderr_artifact,
            stdout=trajectory.summary,
            stderr=stderr,
        ),
        trajectory,
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_all(destination: BinaryIO, payload: bytes) -> None:
    view = memoryview(payload)
    written = 0
    while written < len(view):
        count = destination.write(view[written:])
        if count is None:
            raise OSError("binary stdout destination returned no write count")
        if count <= 0:
            raise OSError("binary stdout destination made no write progress")
        written += count
