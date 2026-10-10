from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

import pytest

from projectkoios.simulations.dft.pseudopotential import (
    Pseudopotential,
    PseudopotentialArtifactFormat,
    PseudopotentialFile,
)
from projectkoios.simulations.dft.pseudopotential.library import (
    PseudopotentialLibrary,
)
from projectkoios.simulations.dft.pw.scf.specification import PwDftScfSpecification
from projectkoios.simulations.library import (
    AuthoredSimulationProvenance,
    SimulationConflictError,
    SimulationDependencyError,
    SimulationIntegrityError,
    SimulationJsonCodec,
    SimulationLibrary,
    SimulationLibraryEntry,
    SimulationLibraryManifestLoader,
    SimulationManifestError,
    SimulationNotFoundError,
    SimulationRecord,
    SimulationRepresentation,
)
from projectkoios.simulations.structure import (
    StructureLibrary,
    StructureLibraryEntry,
)
from tests.projectkoios.simulations.dft.pw.support import (
    silicon_structure_resolution,
)
from tests.projectkoios.simulations.library.support import silicon_scf_specification


def test_resolves_exact_specification_and_every_scientific_dependency(
    tmp_path: Path,
) -> None:
    specification, content, record, structure_library, pseudopotential_library = (
        _fixture(tmp_path)
    )
    library = SimulationLibrary(
        root=tmp_path,
        entries=(SimulationLibraryEntry(record, "simulation.json"),),
    )

    resolution = library.resolve(
        record,
        structure_library=structure_library,
        pseudopotential_library=pseudopotential_library,
    )

    assert resolution.record is record
    assert resolution.path == (tmp_path / "simulation.json").resolve()
    assert resolution.specification == specification
    assert resolution.structure.record == specification.simulation.structure
    assert resolution.pseudopotentials == (
        (
            specification.simulation.pseudopotentials[0],
            tmp_path / "pseudopotentials" / "Si.upf",
        ),
    )
    assert library.records() == (record,)
    assert library.require_unique(record.simulation_id) is record
    assert len(content) == record.byte_size


def test_requires_an_exact_record_when_a_stable_identifier_has_history(
    tmp_path: Path,
) -> None:
    first, _, first_record, structures, pseudopotentials = _fixture(tmp_path)
    second = replace(first, wavefunction_cutoff_ev=500.0)
    second_content = SimulationJsonCodec().dumps(second)
    (tmp_path / "second.json").write_bytes(second_content)
    second_record = _record(second.simulation_id, second_content)
    library = SimulationLibrary(
        root=tmp_path,
        entries=(
            SimulationLibraryEntry(first_record, "simulation.json"),
            SimulationLibraryEntry(second_record, "second.json"),
        ),
    )

    assert library.records(first.simulation_id) == (first_record, second_record)
    with pytest.raises(SimulationConflictError, match="multiple exact records"):
        library.require_unique(first.simulation_id)
    assert (
        library.resolve(
            second_record,
            structure_library=structures,
            pseudopotential_library=pseudopotentials,
        ).specification
        == second
    )


def test_reports_undeclared_missing_changed_and_symlinked_records(
    tmp_path: Path,
) -> None:
    specification, content, record, structures, pseudopotentials = _fixture(tmp_path)
    path = tmp_path / "simulation.json"
    library = SimulationLibrary(
        root=tmp_path,
        entries=(SimulationLibraryEntry(record, path.name),),
    )
    other_content = SimulationJsonCodec().dumps(
        replace(specification, wavefunction_cutoff_ev=401.0)
    )
    other_record = _record(specification.simulation_id, other_content)

    with pytest.raises(SimulationNotFoundError, match="not declared"):
        library.resolve(
            other_record,
            structure_library=structures,
            pseudopotential_library=pseudopotentials,
        )
    with pytest.raises(SimulationNotFoundError, match="not declared"):
        library.require_unique("Si.Other.SCF")

    path.write_bytes(bytes(byte ^ 1 for byte in content))
    with pytest.raises(SimulationIntegrityError, match="SHA-256 mismatch"):
        library.resolve(
            record,
            structure_library=structures,
            pseudopotential_library=pseudopotentials,
        )

    path.unlink()
    target = tmp_path / "target.json"
    target.write_bytes(content)
    path.symlink_to(target)
    with pytest.raises(SimulationNotFoundError, match="unavailable"):
        library.resolve(
            record,
            structure_library=structures,
            pseudopotential_library=pseudopotentials,
        )


def test_rejects_decoded_identity_and_representation_mismatches(
    tmp_path: Path,
) -> None:
    specification, content, record, structures, pseudopotentials = _fixture(tmp_path)

    wrong_representation = _record(
        specification.simulation_id,
        content,
        representation=SimulationRepresentation.PW_DFT_RELAXATION,
    )
    library = SimulationLibrary(
        root=tmp_path,
        entries=(SimulationLibraryEntry(wrong_representation, "simulation.json"),),
    )
    with pytest.raises(SimulationIntegrityError, match="representation"):
        library.resolve(
            wrong_representation,
            structure_library=structures,
            pseudopotential_library=pseudopotentials,
        )

    wrong_identifier = _record("Si.Other.SCF", content)
    library = SimulationLibrary(
        root=tmp_path,
        entries=(SimulationLibraryEntry(wrong_identifier, "simulation.json"),),
    )
    with pytest.raises(SimulationIntegrityError, match="simulation_id"):
        library.resolve(
            wrong_identifier,
            structure_library=structures,
            pseudopotential_library=pseudopotentials,
        )
    assert record.sha256 == wrong_identifier.sha256


def test_fails_closed_when_exact_dependencies_are_unavailable(tmp_path: Path) -> None:
    _, _, record, structures, pseudopotentials = _fixture(tmp_path)
    library = SimulationLibrary(
        root=tmp_path,
        entries=(SimulationLibraryEntry(record, "simulation.json"),),
    )
    empty_structures_root = tmp_path / "empty-structures"
    empty_structures_root.mkdir()
    empty_pseudopotentials_root = tmp_path / "empty-pseudopotentials"
    empty_pseudopotentials_root.mkdir()

    with pytest.raises(SimulationDependencyError, match="structure"):
        library.resolve(
            record,
            structure_library=StructureLibrary(empty_structures_root, ()),
            pseudopotential_library=pseudopotentials,
        )
    empty_pseudopotential_library = PseudopotentialLibrary(empty_pseudopotentials_root)
    with pytest.raises(SimulationDependencyError, match="pseudopotential"):
        library.resolve(
            record,
            structure_library=structures,
            pseudopotential_library=empty_pseudopotential_library,
        )

    (empty_pseudopotentials_root / "Si.upf").write_bytes(b"wrong exact bytes")
    with pytest.raises(SimulationDependencyError, match="none matched"):
        library.resolve(
            record,
            structure_library=structures,
            pseudopotential_library=empty_pseudopotential_library,
        )


def test_authenticates_and_loads_a_strict_manifest(tmp_path: Path) -> None:
    specification, content, record, structures, pseudopotentials = _fixture(tmp_path)
    manifest = _write_manifest(tmp_path, record)
    manifest_content = manifest.read_bytes()

    library = SimulationLibraryManifestLoader(
        manifest_path=manifest,
        expected_sha256=hashlib.sha256(manifest_content).hexdigest(),
        expected_byte_size=len(manifest_content),
    ).load()

    assert library.records() == (record,)
    assert (
        library.resolve_unique(
            specification.simulation_id,
            structure_library=structures,
            pseudopotential_library=pseudopotentials,
        ).specification
        == specification
    )
    assert hashlib.sha256(content).hexdigest() == record.sha256


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("expected_byte_size", 1, "byte-size mismatch"),
        ("expected_sha256", "0" * 64, "SHA-256 mismatch"),
        ("maximum_manifest_bytes", 1, "exceeds the byte limit"),
    ),
)
def test_rejects_unauthenticated_or_oversized_manifests(
    tmp_path: Path,
    field: str,
    value: int | str,
    message: str,
) -> None:
    _, _, record, _, _ = _fixture(tmp_path)
    manifest = _write_manifest(tmp_path, record)
    content = manifest.read_bytes()
    arguments: dict[str, object] = {
        "manifest_path": manifest,
        "expected_sha256": hashlib.sha256(content).hexdigest(),
        "expected_byte_size": len(content),
    }
    arguments[field] = value

    with pytest.raises(SimulationManifestError, match=message):
        SimulationLibraryManifestLoader(**arguments).load()  # type: ignore[arg-type]


def test_rejects_a_manifest_replaced_by_a_symlink_after_construction(
    tmp_path: Path,
) -> None:
    _, _, record, _, _ = _fixture(tmp_path)
    manifest = _write_manifest(tmp_path, record)
    content = manifest.read_bytes()
    loader = SimulationLibraryManifestLoader(
        manifest,
        hashlib.sha256(content).hexdigest(),
        len(content),
    )
    target = tmp_path / "target-catalog.toml"
    target.write_bytes(content)
    manifest.unlink()
    manifest.symlink_to(target)

    with pytest.raises(SimulationManifestError, match="symlink"):
        loader.load()


def test_rejects_unknown_manifest_keys_and_record_path_traversal(
    tmp_path: Path,
) -> None:
    _, _, record, _, _ = _fixture(tmp_path)
    manifest = _write_manifest(tmp_path, record)
    manifest.write_text(
        manifest.read_text(encoding="utf-8") + "unknown = true\n",
        encoding="utf-8",
    )
    content = manifest.read_bytes()

    with pytest.raises(SimulationManifestError, match="keys are invalid"):
        SimulationLibraryManifestLoader(
            manifest,
            hashlib.sha256(content).hexdigest(),
            len(content),
        ).load()
    with pytest.raises(ValueError, match="normalized relative POSIX path"):
        SimulationLibraryEntry(record, "../simulation.json")


def test_enforces_the_record_byte_limit_before_resolution(tmp_path: Path) -> None:
    _, content, record, _, _ = _fixture(tmp_path)

    with pytest.raises(ValueError, match="exceeds maximum_record_bytes"):
        SimulationLibrary(
            root=tmp_path,
            entries=(SimulationLibraryEntry(record, "simulation.json"),),
            maximum_record_bytes=len(content) - 1,
        )


def _fixture(
    root: Path,
) -> tuple[
    PwDftScfSpecification,
    bytes,
    SimulationRecord,
    StructureLibrary,
    PseudopotentialLibrary,
]:
    pseudopotential_content = b"exact silicon pseudopotential"
    pseudopotential = PseudopotentialFile(
        pseudopotential=Pseudopotential(
            symbol="Si",
            exchange_correlation="PBE",
            formalism="ultrasoft",
            relativistic_treatment="scalar-relativistic",
            valence_electrons=4,
        ),
        artifact_format=PseudopotentialArtifactFormat.UPF,
        artifact_format_version="2.0.1",
        filename="Si.upf",
        sha256=hashlib.sha256(pseudopotential_content).hexdigest(),
        byte_size=len(pseudopotential_content),
    )
    base = silicon_scf_specification()
    specification = replace(
        base,
        simulation=replace(
            base.simulation,
            pseudopotentials=(pseudopotential,),
        ),
    )
    content = SimulationJsonCodec().dumps(specification)
    (root / "simulation.json").write_bytes(content)
    record = _record(specification.simulation_id, content)

    structure = silicon_structure_resolution()
    structure_library = StructureLibrary(
        root=structure.path.parent,
        entries=(
            StructureLibraryEntry(
                structure.record,
                structure.path.name,
            ),
        ),
    )
    pseudopotential_root = root / "pseudopotentials"
    pseudopotential_root.mkdir()
    (pseudopotential_root / pseudopotential.filename).write_bytes(
        pseudopotential_content
    )
    return (
        specification,
        content,
        record,
        structure_library,
        PseudopotentialLibrary(pseudopotential_root),
    )


def _record(
    simulation_id: str,
    content: bytes,
    *,
    representation: SimulationRepresentation = SimulationRepresentation.PW_DFT_SCF,
) -> SimulationRecord:
    sha256 = hashlib.sha256(content).hexdigest()
    return SimulationRecord(
        simulation_id=simulation_id,
        representation=representation,
        schema_version=1,
        byte_size=len(content),
        sha256=sha256,
        provenance=AuthoredSimulationProvenance(
            source="tests/projectkoios/simulations/library",
            author="ProjectKoios maintainers",
            result_sha256=sha256,
        ),
    )


def _write_manifest(root: Path, record: SimulationRecord) -> Path:
    manifest = root / "catalog.toml"
    manifest.write_text(
        f'''schema_version = 1

[[records]]
simulation_id = "{record.simulation_id}"
representation = "{record.representation.value}"
schema_version = {record.schema_version}
byte_size = {record.byte_size}
sha256 = "{record.sha256}"
relative_path = "simulation.json"

[records.provenance]
kind = "authored"
source = "tests/projectkoios/simulations/library"
author = "ProjectKoios maintainers"
result_sha256 = "{record.sha256}"
''',
        encoding="utf-8",
    )
    return manifest.resolve()
