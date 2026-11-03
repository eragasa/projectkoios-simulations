from __future__ import annotations

import hashlib
import os
import tempfile
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from projectkoios.simulations.execution import (
    CalculatorExecutableBinding,
    CalculatorExecutableIdentity,
    CalculatorExecutablePreparationFailure,
    CalculatorExecutablePreparationFailureCode,
    CalculatorExecutablePreparer,
    CalculatorPreparedExecutable,
)


class TestCalculatorExecutablePreparer:
    """Verify exact executable preparation without process entry.

    Notes
    -----
    The deterministic files in these tests are controlled software fixtures, not
    scientific calculators. Passing tests establish only read-only identity and
    filesystem behavior.
    """

    def _binding(
        self,
        path: Path,
        *,
        expected_content: bytes,
    ) -> CalculatorExecutableBinding:
        """Construct one exact executable binding for a controlled file.

        Parameters
        ----------
        path
            Absolute controlled fixture path.
        expected_content
            Bytes declared as the exact executable identity.

        Returns
        -------
        CalculatorExecutableBinding
            Exact immutable identity bound to ``path``.
        """
        return CalculatorExecutableBinding(
            identity=CalculatorExecutableIdentity(
                calculator_name="controlled executable",
                calculator_version="fixture-1",
                byte_size=len(expected_content),
                sha256=hashlib.sha256(expected_content).hexdigest(),
            ),
            path=path,
        )

    def test__CalculatorExecutablePreparer__verifies_exact_regular_file(self) -> None:
        """Verify matching executable bytes and retain immutable mode evidence."""
        content = b"#!/bin/sh\nexit 0\n"
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "controlled-executable"
            path.write_bytes(content)
            path.chmod(0o500)
            result = CalculatorExecutablePreparer(
                self._binding(path, expected_content=content)
            ).prepare()

        assert type(result) is CalculatorPreparedExecutable
        assert result.observed_mode == 0o500
        with pytest.raises(FrozenInstanceError):
            result.observed_mode = 0o700  # type: ignore[misc]

    def test__CalculatorExecutablePreparer__rejects_symbolic_link(self) -> None:
        """Reject a symbolic-link deployment path without following its target."""
        content = b"#!/bin/sh\nexit 0\n"
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            target = root / "target"
            target.write_bytes(content)
            target.chmod(0o500)
            link = root / "executable"
            link.symlink_to(target)
            result = CalculatorExecutablePreparer(
                self._binding(link, expected_content=content)
            ).prepare()

        assert result == CalculatorExecutablePreparationFailure(
            binding=self._binding(link, expected_content=content),
            code=CalculatorExecutablePreparationFailureCode.SYMBOLIC_LINK,
            observed_condition="executable path is a symbolic link",
        )

    def test__CalculatorExecutablePreparer__rejects_nonexecutable_mode(self) -> None:
        """Reject exact bytes when the regular file has no executable mode bit."""
        content = b"controlled bytes"
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "controlled-executable"
            path.write_bytes(content)
            path.chmod(0o400)
            result = CalculatorExecutablePreparer(
                self._binding(path, expected_content=content)
            ).prepare()

        assert type(result) is CalculatorExecutablePreparationFailure
        assert result.code is CalculatorExecutablePreparationFailureCode.NOT_EXECUTABLE

    def test__CalculatorExecutablePreparer__rejects_content_mismatch(self) -> None:
        """Distinguish byte-size and digest mismatches without process entry."""
        content = b"controlled bytes"
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            size_path = root / "size-mismatch"
            size_path.write_bytes(content + b"!")
            size_path.chmod(0o500)
            digest_path = root / "digest-mismatch"
            digest_path.write_bytes(b"different bytes")
            digest_path.chmod(0o500)
            size_result = CalculatorExecutablePreparer(
                self._binding(size_path, expected_content=content)
            ).prepare()
            digest_result = CalculatorExecutablePreparer(
                self._binding(
                    digest_path,
                    expected_content=b"alternate bytes",
                )
            ).prepare()

        assert (
            type(size_result) is CalculatorExecutablePreparationFailure
            and size_result.code
            is CalculatorExecutablePreparationFailureCode.BYTE_SIZE_MISMATCH
        )
        assert (
            type(digest_result) is CalculatorExecutablePreparationFailure
            and digest_result.code
            is CalculatorExecutablePreparationFailureCode.SHA256_MISMATCH
        )

    def test__CalculatorExecutablePreparer__does_not_invoke_executable(self) -> None:
        """Observe bytes without entering the controlled executable process."""
        content = b"#!/bin/sh\nprintf invoked > marker\n"
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            path = root / "controlled-executable"
            path.write_bytes(content)
            path.chmod(0o500)
            previous = Path.cwd()
            try:
                os.chdir(root)
                result = CalculatorExecutablePreparer(
                    self._binding(path, expected_content=content)
                ).prepare()
            finally:
                os.chdir(previous)

            assert type(result) is CalculatorPreparedExecutable
            assert not (root / "marker").exists()
