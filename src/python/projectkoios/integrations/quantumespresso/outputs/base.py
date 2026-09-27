"""Nominal bases shared by Quantum ESPRESSO output-file families."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import PurePosixPath

_PREFIX = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")


class QuantumEspressoOutputFileError(ValueError):
    """Report captured output from which supported evidence cannot be read."""


@dataclass(frozen=True, slots=True)
class QeOutputFile:
    """Nominal base for one safe calculator-native relative output path."""

    relative_path: str

    def __post_init__(self) -> None:
        if type(self.relative_path) is not str or not self.relative_path:
            raise ValueError("relative_path must be a nonempty string")
        if "\\" in self.relative_path:
            raise ValueError("relative_path must use POSIX separators")
        path = PurePosixPath(self.relative_path)
        if path.is_absolute() or path == PurePosixPath(".") or ".." in path.parts:
            raise ValueError("relative_path must be a safe relative path")

    @staticmethod
    def _validate_prefix(prefix: str) -> None:
        if type(prefix) is not str or not _PREFIX.fullmatch(prefix):
            raise ValueError("prefix must be safe for one output filename")

    @staticmethod
    def _join(directory: str, filename: str) -> str:
        if type(directory) is not str:
            raise TypeError("directory must be a string")
        if not directory:
            return filename
        return str(PurePosixPath(directory) / filename)


@dataclass(frozen=True, slots=True)
class QeOutputFileResult[OutputFileT: QeOutputFile]:
    """Nominal base for observations extracted from one declared output file."""

    output_file: OutputFileT

    def __post_init__(self) -> None:
        if not isinstance(self.output_file, QeOutputFile):
            raise TypeError("output_file must be a QeOutputFile")


class QeOutputFileParser[OutputFileT: QeOutputFile](ABC):
    """Nominal generic base for one output-file parser implementation."""

    @abstractmethod
    def parse(
        self,
        payload: bytes,
        *,
        output_file: OutputFileT,
    ) -> QeOutputFileResult[OutputFileT]:
        """Parse one bounded payload correlated to its file declaration."""
