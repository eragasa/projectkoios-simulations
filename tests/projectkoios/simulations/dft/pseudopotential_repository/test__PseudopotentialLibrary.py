from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from projectkoios.simulations.dft.pseudopotential import (
    Pseudopotential,
    PseudopotentialFile,
)
from projectkoios.simulations.dft.pseudopotential_repository import (
    PseudopotentialIntegrityError,
    PseudopotentialLibrary,
    PseudopotentialNotFoundError,
)


class PseudopotentialLibraryTest(unittest.TestCase):
    def test_finds_exact_bytes_beneath_a_nested_library_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            efficiency = root / "sets" / "PBE" / "efficiency" / "Si.upf"
            precision = root / "sets" / "PBE" / "precision" / "Si.upf"
            efficiency.parent.mkdir(parents=True)
            precision.parent.mkdir(parents=True)
            content = b"verified pseudopotential"
            efficiency.write_bytes(content)
            precision.write_bytes(content)
            required = _file(content)

            resolved = PseudopotentialLibrary(root).resolve(required)

            self.assertEqual(resolved, efficiency)

    def test_rejects_same_named_files_with_different_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            path = root / "sets" / "Si.upf"
            path.parent.mkdir()
            path.write_bytes(b"other pseudopotential")

            with self.assertRaisesRegex(
                PseudopotentialIntegrityError,
                "none matched",
            ):
                PseudopotentialLibrary(root).resolve(_file(b"required bytes"))

    def test_reports_an_unavailable_required_filename(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)

            with self.assertRaisesRegex(
                PseudopotentialNotFoundError,
                "unavailable beneath the library",
            ):
                PseudopotentialLibrary(root).resolve(_file(b"required bytes"))

    def test_builds_an_exact_repository_for_the_required_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            path = root / "installed" / "Si.upf"
            path.parent.mkdir()
            content = b"verified pseudopotential"
            path.write_bytes(content)
            required = _file(content)

            repository = PseudopotentialLibrary(root).build_repository((required,))

            self.assertEqual(repository.resolve(required), path)

    def test_rejects_a_symlink_as_the_library_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            parent = Path(temporary_directory)
            target = parent / "target"
            target.mkdir()
            alias = parent / "alias"
            alias.symlink_to(target, target_is_directory=True)

            with self.assertRaisesRegex(ValueError, "nonsymlink directory"):
                PseudopotentialLibrary(alias)


def _file(content: bytes) -> PseudopotentialFile:
    return PseudopotentialFile(
        pseudopotential=Pseudopotential(
            symbol="Si",
            exchange_correlation="PBE",
            formalism="ultrasoft",
            relativistic_treatment="scalar-relativistic",
            valence_electrons=4,
        ),
        filename="Si.upf",
        sha256=hashlib.sha256(content).hexdigest(),
        byte_size=len(content),
    )


if __name__ == "__main__":
    unittest.main()
