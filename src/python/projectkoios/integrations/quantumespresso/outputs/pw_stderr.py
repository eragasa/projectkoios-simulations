"""File, parser, and result composition for captured ``pw.x`` stderr."""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from projectkoios.integrations.quantumespresso.outputs.base import (
    QeOutputFile,
    QeOutputFileParser,
    QeOutputFileResult,
    QuantumEspressoOutputFileError,
)

_MAX_OUTPUT_BYTES = 100_000_000
_IEEE_FLAGS = (
    "IEEE_INVALID_FLAG",
    "IEEE_DIVIDE_BY_ZERO",
    "IEEE_OVERFLOW_FLAG",
    "IEEE_UNDERFLOW_FLAG",
)


@final
@dataclass(frozen=True, slots=True)
class QePwStderrFile(QeOutputFile):
    """Declare one captured ``pw.x`` standard-error file."""


@final
@dataclass(frozen=True, slots=True)
class QePwStderrFileResult(QeOutputFileResult[QePwStderrFile]):
    """Represent structured warnings from one captured ``pw.x`` stderr file."""

    ieee_flags: tuple[str, ...]

    def __post_init__(self) -> None:
        super(QePwStderrFileResult, self).__post_init__()
        if type(self.output_file) is not QePwStderrFile:
            raise TypeError("output_file must be a QePwStderrFile")
        if type(self.ieee_flags) is not tuple:
            raise TypeError("ieee_flags must be a tuple")
        if any(flag not in _IEEE_FLAGS for flag in self.ieee_flags):
            raise ValueError("ieee_flags contains an unsupported flag")
        if len(set(self.ieee_flags)) != len(self.ieee_flags):
            raise ValueError("ieee_flags must not contain duplicates")


@final
@dataclass(frozen=True, slots=True)
class QePwStderrFileParser(QeOutputFileParser[QePwStderrFile]):
    """Parse one bounded captured ``pw.x`` standard-error file."""

    def parse(
        self,
        payload: bytes,
        *,
        output_file: QePwStderrFile,
    ) -> QePwStderrFileResult:
        """Return represented IEEE flags in deterministic declaration order."""
        if type(payload) is not bytes:
            raise TypeError("pw.x stderr payload must be bytes")
        if len(payload) > _MAX_OUTPUT_BYTES:
            raise QuantumEspressoOutputFileError("pw.x stderr exceeds the byte limit")
        if type(output_file) is not QePwStderrFile:
            raise TypeError("output_file must be a QePwStderrFile")
        text = payload.decode("utf-8")
        return QePwStderrFileResult(
            output_file=output_file,
            ieee_flags=tuple(flag for flag in _IEEE_FLAGS if flag in text),
        )
