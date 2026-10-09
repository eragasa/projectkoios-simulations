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

    def test_rejects_invalid_library_roots_in_validation_order(self) -> None:
        with self.assertRaisesRegex(TypeError, "root must be a Path"):
            PseudopotentialLibrary("/tmp")  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "root must be absolute"):
            PseudopotentialLibrary(Path("relative"))

        with tempfile.TemporaryDirectory() as temporary_directory:
            parent = Path(temporary_directory)
            missing = parent / "missing"
            with self.assertRaisesRegex(ValueError, "nonsymlink directory"):
                PseudopotentialLibrary(missing)

            target = parent / "target"
            target.mkdir()
            alias = parent / "alias"
            alias.symlink_to(target, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "nonsymlink directory"):
                PseudopotentialLibrary(alias)

    def test_rejects_a_symlink_candidate_even_when_its_target_matches(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            parent = Path(temporary_directory)
            root = parent / "library"
            root.mkdir()
            content = b"verified pseudopotential"
            target = parent / "outside.upf"
            target.write_bytes(content)
            (root / "Si.upf").symlink_to(target)

            with self.assertRaisesRegex(
                PseudopotentialIntegrityError,
                "none matched",
            ):
                PseudopotentialLibrary(root).resolve(_file(content))

    def test_rejects_invalid_requirements_and_accepts_an_empty_tuple(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            library = PseudopotentialLibrary(Path(temporary_directory))

            with self.assertRaisesRegex(
                TypeError,
                "required must inherit from PseudopotentialFile",
            ):
                library.resolve(object())  # type: ignore[arg-type]
            with self.assertRaisesRegex(TypeError, "required must be a tuple"):
                library.build_repository([])  # type: ignore[arg-type]
            with self.assertRaisesRegex(
                TypeError,
                "required must contain PseudopotentialFile values",
            ):
                library.build_repository((object(),))  # type: ignore[arg-type]

            self.assertEqual(library.build_repository(()).entries, ())

    def test_rejects_duplicate_resolved_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            content = b"verified pseudopotential"
            (root / "Si.upf").write_bytes(content)
            required = _file(content)

            with self.assertRaisesRegex(ValueError, "unique across metadata"):
                PseudopotentialLibrary(root).build_repository((required, required))


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
