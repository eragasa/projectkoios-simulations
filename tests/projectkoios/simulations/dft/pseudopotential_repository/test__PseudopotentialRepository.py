from __future__ import annotations

import hashlib
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from projectkoios.simulations.dft.pseudopotential import (
    Pseudopotential,
    PseudopotentialFile,
)
from projectkoios.simulations.dft.pseudopotential_repository import (
    PseudopotentialIntegrityError,
    PseudopotentialNotFoundError,
    PseudopotentialRepository,
    PseudopotentialRepositoryEntry,
)


class PseudopotentialRepositoryTest(unittest.TestCase):
    def test_resolves_and_verifies_an_exact_declared_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "Si.upf"
            path.write_bytes(b"verified pseudopotential")
            required = _file(path.read_bytes())
            repository = PseudopotentialRepository(
                entries=(
                    PseudopotentialRepositoryEntry(
                        pseudopotential_file=required,
                        path=path,
                    ),
                )
            )

            self.assertEqual(repository.resolve(required), path)

    def test_raises_when_the_declared_artifact_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            missing = Path(temporary_directory) / "Si.upf"
            required = _file(b"expected bytes")
            repository = PseudopotentialRepository(
                entries=(
                    PseudopotentialRepositoryEntry(
                        pseudopotential_file=required,
                        path=missing,
                    ),
                )
            )

            with self.assertRaisesRegex(PseudopotentialNotFoundError, "unavailable"):
                repository.resolve(required)

    def test_raises_when_the_declared_artifact_has_changed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "Si.upf"
            path.write_bytes(b"changed bytes")
            required = _file(b"expected bytes")
            repository = PseudopotentialRepository(
                entries=(
                    PseudopotentialRepositoryEntry(
                        pseudopotential_file=required,
                        path=path,
                    ),
                )
            )

            with self.assertRaises(PseudopotentialIntegrityError):
                repository.resolve(required)

    def test_rejects_conflicting_scientific_metadata_for_the_same_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "Si.upf"
            content = b"verified pseudopotential"
            path.write_bytes(content)
            declared = _file(content)
            repository = PseudopotentialRepository(
                entries=(
                    PseudopotentialRepositoryEntry(
                        pseudopotential_file=declared,
                        path=path,
                    ),
                )
            )
            metadata_conflicts = (
                replace(declared.pseudopotential, exchange_correlation="LDA"),
                replace(declared.pseudopotential, formalism="PAW"),
                replace(
                    declared.pseudopotential,
                    relativistic_treatment="fully-relativistic",
                ),
                replace(declared.pseudopotential, valence_electrons=14),
            )

            for conflicting_metadata in metadata_conflicts:
                required = replace(
                    declared,
                    pseudopotential=conflicting_metadata,
                )
                with (
                    self.subTest(required=required),
                    self.assertRaises(PseudopotentialNotFoundError),
                ):
                    repository.resolve(required)
                with (
                    self.subTest(conflicting_declaration=required),
                    self.assertRaisesRegex(ValueError, "unique across metadata"),
                ):
                    PseudopotentialRepository(
                        entries=(
                            PseudopotentialRepositoryEntry(declared, path),
                            PseudopotentialRepositoryEntry(required, path),
                        )
                    )


def _file(content: bytes) -> PseudopotentialFile:
    return PseudopotentialFile(
        pseudopotential=Pseudopotential(
            symbol="Si",
            exchange_correlation="PBE",
            formalism="ONCVPSP",
            relativistic_treatment="scalar-relativistic",
            valence_electrons=4,
        ),
        filename="Si.upf",
        sha256=hashlib.sha256(content).hexdigest(),
        byte_size=len(content),
    )


if __name__ == "__main__":
    unittest.main()
