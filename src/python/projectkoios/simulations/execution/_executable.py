"""Exact executable identity and read-only preparation records."""

from __future__ import annotations

import errno
import hashlib
import os
import re
import stat
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import BinaryIO

from projectkoios.physkit.core.data import DataObject
from projectkoios.physkit.core.results import ResultsObject

_SHA256 = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True, slots=True)
class CalculatorExecutableIdentity(DataObject):
    """Identify exact executable bytes in one calculator version namespace.

    Parameters
    ----------
    calculator_name
        Nonempty calculator or executable family name.
    calculator_version
        Exact nonempty version represented by the executable bytes.
    byte_size
        Positive executable file size in bytes.
    sha256
        Lowercase hexadecimal SHA-256 digest of the executable bytes.

    Notes
    -----
    This record identifies bytes only. It does not establish calculator
    compatibility, grant execution authority, or validate scientific behavior.
    """

    calculator_name: str
    calculator_version: str
    byte_size: int
    sha256: str

    def __post_init__(self) -> None:
        for label, value in (
            ("calculator_name", self.calculator_name),
            ("calculator_version", self.calculator_version),
        ):
            if type(value) is not str or not value or value != value.strip():
                raise ValueError(f"{label} must be nonempty and stripped")
        if type(self.byte_size) is not int or self.byte_size <= 0:
            raise ValueError("byte_size must be a positive integer")
        if type(self.sha256) is not str or not _SHA256.fullmatch(self.sha256):
            raise ValueError("sha256 must be lowercase hexadecimal")


@dataclass(frozen=True, slots=True)
class CalculatorExecutableBinding(DataObject):
    """Bind an exact executable identity to one absolute deployment path.

    Parameters
    ----------
    identity
        Exact expected executable bytes and calculator version namespace.
    path
        Absolute lexical deployment path inspected during preparation.

    Notes
    -----
    Construction performs no filesystem observation. The separate preparer owns
    mutable deployment-state inspection and returns a typed result.
    """

    identity: CalculatorExecutableIdentity
    path: Path

    def __post_init__(self) -> None:
        if type(self.identity) is not CalculatorExecutableIdentity:
            raise TypeError("identity must be a CalculatorExecutableIdentity")
        if not isinstance(self.path, Path):
            raise TypeError("path must be a Path")
        if not self.path.is_absolute() or ".." in self.path.parts:
            raise ValueError("path must be absolute without parent traversal")


class CalculatorExecutablePreparationFailureCode(StrEnum):
    """Classify read-only executable preparation failures."""

    MISSING = "missing"
    SYMBOLIC_LINK = "symbolic-link"
    NOT_REGULAR = "not-regular"
    NOT_EXECUTABLE = "not-executable"
    BYTE_SIZE_MISMATCH = "byte-size-mismatch"
    SHA256_MISMATCH = "sha256-mismatch"
    OBSERVATION_FAILED = "observation-failed"


@dataclass(frozen=True, slots=True)
class CalculatorExecutablePreparationFailure(ResultsObject):
    """Represent one fail-closed executable preparation result.

    Parameters
    ----------
    binding
        Exact executable binding that could not be established.
    code
        Stable mechanical preparation-failure classification.
    observed_condition
        Nonempty sanitized description of the failed observation.
    """

    binding: CalculatorExecutableBinding
    code: CalculatorExecutablePreparationFailureCode
    observed_condition: str

    def __post_init__(self) -> None:
        if type(self.binding) is not CalculatorExecutableBinding:
            raise TypeError("binding must be a CalculatorExecutableBinding")
        if type(self.code) is not CalculatorExecutablePreparationFailureCode:
            raise TypeError("code must be a CalculatorExecutablePreparationFailureCode")
        if (
            type(self.observed_condition) is not str
            or not self.observed_condition
            or self.observed_condition != self.observed_condition.strip()
        ):
            raise ValueError("observed_condition must be nonempty and stripped")


@dataclass(frozen=True, slots=True)
class CalculatorPreparedExecutable(ResultsObject):
    """Record successful read-only verification of exact executable bytes.

    Parameters
    ----------
    binding
        Exact identity and deployment path that were observed.
    observed_mode
        Nonnegative POSIX mode bits observed for the regular executable file.

    Notes
    -----
    This result records a read-only observation. Mutable filesystem state may
    change afterward, so a staging or execution owner must close its own
    time-of-check/time-of-use boundary before process entry.
    """

    binding: CalculatorExecutableBinding
    observed_mode: int

    def __post_init__(self) -> None:
        if type(self.binding) is not CalculatorExecutableBinding:
            raise TypeError("binding must be a CalculatorExecutableBinding")
        if type(self.observed_mode) is not int or not 0 <= self.observed_mode <= 0o7777:
            raise ValueError("observed_mode must contain nonnegative POSIX mode bits")
        if self.observed_mode & 0o111 == 0:
            raise ValueError("observed_mode must include an executable bit")


type CalculatorExecutablePreparationResult = (
    CalculatorPreparedExecutable | CalculatorExecutablePreparationFailure
)


@dataclass(frozen=True, slots=True)
class CalculatorExecutablePreparer:
    """Verify one exact executable binding without invoking a process.

    Parameters
    ----------
    binding
        Exact executable identity and absolute deployment path to inspect.

    Notes
    -----
    Preparation is read-only and grants no execution authority. The digest is
    computed from the opened file after its type, mode, and byte size have been
    checked. A consumer that later stages or executes the file must re-establish
    identity at that effect boundary.
    """

    binding: CalculatorExecutableBinding

    def __post_init__(self) -> None:
        if type(self.binding) is not CalculatorExecutableBinding:
            raise TypeError("binding must be a CalculatorExecutableBinding")

    def prepare(self) -> CalculatorExecutablePreparationResult:
        """Return a verified executable observation or typed failure.

        Returns
        -------
        CalculatorExecutablePreparationResult
            Successful exact read-only observation or a fail-closed mechanical
            preparation failure.
        """
        path = self.binding.path
        try:
            metadata = path.lstat()
        except FileNotFoundError:
            return self._failure(
                CalculatorExecutablePreparationFailureCode.MISSING,
                "executable path does not exist",
            )
        except OSError:
            return self._failure(
                CalculatorExecutablePreparationFailureCode.OBSERVATION_FAILED,
                "executable metadata could not be observed",
            )

        # Use lstat-derived mode bits so a symbolic link can never be admitted by
        # following it to a regular executable target.
        if stat.S_ISLNK(metadata.st_mode):
            return self._failure(
                CalculatorExecutablePreparationFailureCode.SYMBOLIC_LINK,
                "executable path is a symbolic link",
            )
        if not stat.S_ISREG(metadata.st_mode):
            return self._failure(
                CalculatorExecutablePreparationFailureCode.NOT_REGULAR,
                "executable path is not a regular file",
            )
        if metadata.st_mode & 0o111 == 0:
            return self._failure(
                CalculatorExecutablePreparationFailureCode.NOT_EXECUTABLE,
                "executable path is not runnable",
            )
        try:
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
            descriptor = os.open(path, flags)
        except FileNotFoundError:
            return self._failure(
                CalculatorExecutablePreparationFailureCode.MISSING,
                "executable path does not exist",
            )
        except OSError as error:
            if error.errno == errno.ELOOP:
                return self._failure(
                    CalculatorExecutablePreparationFailureCode.SYMBOLIC_LINK,
                    "executable path is a symbolic link",
                )
            return self._failure(
                CalculatorExecutablePreparationFailureCode.OBSERVATION_FAILED,
                "executable bytes could not be observed",
            )
        try:
            with os.fdopen(descriptor, "rb") as stream:
                opened_metadata = os.fstat(stream.fileno())
                if not stat.S_ISREG(opened_metadata.st_mode):
                    return self._failure(
                        CalculatorExecutablePreparationFailureCode.NOT_REGULAR,
                        "executable path is not a regular file",
                    )
                if opened_metadata.st_mode & 0o111 == 0:
                    return self._failure(
                        CalculatorExecutablePreparationFailureCode.NOT_EXECUTABLE,
                        "executable path is not runnable",
                    )
                if opened_metadata.st_size != self.binding.identity.byte_size:
                    return self._failure(
                        CalculatorExecutablePreparationFailureCode.BYTE_SIZE_MISMATCH,
                        "executable byte size does not match its identity",
                    )
                digest = self._sha256(stream)
        except OSError:
            return self._failure(
                CalculatorExecutablePreparationFailureCode.OBSERVATION_FAILED,
                "executable bytes could not be observed",
            )
        if digest != self.binding.identity.sha256:
            return self._failure(
                CalculatorExecutablePreparationFailureCode.SHA256_MISMATCH,
                "executable SHA-256 does not match its identity",
            )
        return CalculatorPreparedExecutable(
            binding=self.binding,
            observed_mode=stat.S_IMODE(opened_metadata.st_mode),
        )

    def _failure(
        self,
        code: CalculatorExecutablePreparationFailureCode,
        observed_condition: str,
    ) -> CalculatorExecutablePreparationFailure:
        return CalculatorExecutablePreparationFailure(
            binding=self.binding,
            code=code,
            observed_condition=observed_condition,
        )

    def _sha256(self, stream: BinaryIO) -> str:
        digest = hashlib.sha256()
        # A bounded chunk avoids loading potentially large calculator binaries into
        # memory while preserving exact byte order for the digest.
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
        return digest.hexdigest()
