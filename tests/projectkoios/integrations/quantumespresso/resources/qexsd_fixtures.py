"""Controlled reduced and exact external QEXSD fixtures for software verification."""

from __future__ import annotations

import hashlib
import math
import os
from dataclasses import dataclass, replace
from pathlib import Path

import pytest

from projectkoios.integrations.quantumespresso.qexsd.parsing import (
    QuantumEspressoXsdDocumentParser,
)
from projectkoios.integrations.quantumespresso.qexsd.records import (
    QexsdDocument,
    QexsdSource,
)
from projectkoios.physkit.units import ModelSystemUnitConverter, PhysicalUnit


@dataclass(frozen=True, slots=True)
class QexsdFixtureResources:
    """Own configured paths and exact identities for shared QEXSD test resources."""

    resource_root: Path

    def __post_init__(self) -> None:
        if not isinstance(self.resource_root, Path):
            raise TypeError("resource_root must be a Path")
        if not self.resource_root.is_dir():
            raise ValueError("resource_root must be an existing directory")

    def controlled_path(self, schema_version: str) -> Path:
        """Return one exact maintained reduced-QEXSD resource path."""
        if schema_version not in {"23.03.10", "25.05.21"}:
            raise ValueError("schema_version must identify a controlled QEXSD resource")
        return self.resource_root / f"qexsd-{schema_version}.xml"

    def controlled_bytes(self, schema_version: str) -> bytes:
        """Return exact bytes from one maintained reduced-QEXSD resource."""
        return self.controlled_path(schema_version).read_bytes()

    def controlled_source_bytes(
        self,
        content: bytes | None = None,
    ) -> tuple[str, int]:
        """Return the independent digest and count for controlled fixture bytes."""
        exact_content = (
            self.controlled_bytes("23.03.10") if content is None else content
        )
        return hashlib.sha256(exact_content).hexdigest(), len(exact_content)

    def source(
        self,
        canonical_path: str,
        content: bytes | None = None,
    ) -> QexsdSource:
        """Construct one explicit source from controlled or supplied exact bytes."""
        exact_content = (
            self.controlled_bytes("23.03.10") if content is None else content
        )
        digest, count = self.controlled_source_bytes(exact_content)
        return QexsdSource(canonical_path, digest, count, exact_content)

    def configured_external_path(self, environment_variable: str) -> Path:
        """Return an explicitly configured external artifact path or skip."""
        configured_path = os.environ.get(environment_variable)
        if configured_path is None:
            pytest.skip(f"set {environment_variable} to run external-artifact evidence")
        return Path(configured_path)

    def controlled_document(self, schema_version: str = "25.05.21") -> QexsdDocument:
        """Parse one maintained reduced-QEXSD resource into its native record."""
        return QuantumEspressoXsdDocumentParser(
            self.source(
                f"/controlled/qexsd-{schema_version}.xml",
                self.controlled_bytes(schema_version),
            )
        ).execute()

    def bands_document(self) -> QexsdDocument:
        """Return the nominal QEXSD document used by bands extraction tests."""
        angstrom_to_bohr = ModelSystemUnitConverter.conversion_factor(
            PhysicalUnit("angstrom"),
            PhysicalUnit("bohr"),
        )
        ev_to_hartree = ModelSystemUnitConverter.conversion_factor(
            PhysicalUnit("eV"),
            PhysicalUnit("hartree"),
        )
        band_energies_ev = ((-2.0, 1.0), (-1.5, 1.5), (-1.0, 2.0))
        return replace(
            self.controlled_document(),
            source_path="/test/data-file-schema.xml",
            source_sha256="0" * 64,
            source_byte_count=123,
            producing_application="Quantum ESPRESSO",
            atomic_structure_alat=2.0 * math.pi * angstrom_to_bohr,
            direct_lattice_vectors=(
                (1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                (0.0, 0.0, 1.0),
            ),
            direct_lattice_source_label="output/atomic_structure/cell",
            reciprocal_lattice_coefficients=(
                (1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                (0.0, 0.0, 1.0),
            ),
            reciprocal_lattice_source_label=("output/basis_set/reciprocal_lattice"),
            atoms=((1, "Si", (0.0, 0.0, 0.0)),),
            declared_atom_count=1,
            k_points=(
                (0.0, 0.0, 0.0),
                (0.25, 0.0, 0.0),
                (0.5, 0.0, 0.0),
            ),
            k_point_weights=(1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0),
            k_point_source_label=("output/band_structure/ks_energies/k_point"),
            eigenvalues=tuple(
                tuple(value * ev_to_hartree for value in row)
                for row in band_energies_ev
            ),
            occupations=((1.0, 0.0), (1.0, 0.0), (1.0, 0.0)),
            eigenvalue_source_label=("output/band_structure/ks_energies/eigenvalues"),
            sampled_k_point_count=3,
            band_count=2,
        )

    def nscf_document(self) -> QexsdDocument:
        """Return the nominal QEXSD document used by NSCF extraction tests."""
        return replace(
            self.scf_document(),
            reciprocal_lattice_coefficients=(
                (1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                (0.0, 0.0, 1.0),
            ),
            k_points=((0.0, 0.0, 0.0), (0.5, 0.0, 0.0)),
            k_point_weights=(0.5, 0.5),
            sampled_k_point_count=2,
            k_point_source_label="band_structure/ks_energies/k_point",
            eigenvalues=((-0.4, 0.2), (-0.3, 0.4)),
            occupations=((1.0, 0.0), (1.0, 0.0)),
            eigenvalue_source_label="band_structure/ks_energies",
            band_count=2,
        )

    def final_structure_document(self) -> QexsdDocument:
        """Return the nominal document used by final-structure extraction tests."""
        return replace(
            self.scf_document(),
            source_path="/evidence/data-file-schema.xml",
            direct_lattice_vectors=(
                (2.0, 0.0, 0.0),
                (1.0, 3.0, 0.0),
                (0.5, 1.0, 4.0),
            ),
            atoms=(
                (1, "Si", (0.0, 0.0, 0.0)),
                (2, "Si", (1.375, 2.25, 3.0)),
            ),
        )

    def plane_wave_frame_document(self) -> QexsdDocument:
        """Return the nominal document used by plane-wave frame tests."""
        return replace(
            self.plane_wave_document(),
            source_path="/test/data-file-schema.xml",
            species=(("Si", 28.0855, "Si.pbe-n-van.UPF"),),
            k_points=((0.25, 0.0, 0.0),),
            eigenvalues=(tuple(0.0 for _ in range(12)),),
            band_count=12,
            fft_grid=(4, 4, 4),
        )

    def plane_wave_document(self) -> QexsdDocument:
        """Return the nominal QEXSD document used by plane-wave frame tests."""
        return replace(
            self.controlled_document(),
            source_path="/run/work/qe/si.save/data-file-schema.xml",
            source_sha256="0" * 64,
            source_byte_count=123,
            producing_application="Quantum ESPRESSO",
            atomic_structure_alat=1.0,
            direct_lattice_vectors=(
                (1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                (0.0, 0.0, 1.0),
            ),
            direct_lattice_source_label="output/atomic_structure/cell",
            reciprocal_lattice_coefficients=(
                (1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                (0.0, 0.0, 1.0),
            ),
            reciprocal_lattice_source_label=("output/basis_set/reciprocal_lattice"),
            species=(("Si", 28.0855, "Si.UPF"),),
            atoms=((1, "Si", (0.0, 0.0, 0.0)),),
            declared_atom_count=1,
            k_points=((0.0, 0.0, 0.0),),
            k_point_weights=(1.0,),
            sampled_k_point_count=1,
            k_point_source_label=("output/band_structure/ks_energies/k_point"),
            eigenvalues=((0.0,),),
            occupations=None,
            band_count=1,
            fft_grid=(1, 1, 1),
        )

    def scf_document(self) -> QexsdDocument:
        """Return the nominal QEXSD document used by SCF extraction tests."""
        return replace(
            self.controlled_document(),
            source_path="/retained/data-file-schema.xml",
            source_sha256="a" * 64,
            source_byte_count=123,
            producing_application="Quantum ESPRESSO",
            atomic_structure_alat=2.0,
            direct_lattice_vectors=(
                (2.0, 0.0, 0.0),
                (0.0, 2.0, 0.0),
                (0.0, 0.0, 2.0),
            ),
            direct_lattice_source_label="output/atomic_structure/cell/a1,a2,a3",
            atoms=(
                (1, "Si", (0.0, 0.0, 0.0)),
                (2, "Si", (0.5, 0.5, 0.5)),
            ),
            declared_atom_count=2,
            atomic_positions_source_label=("output/atomic_structure/atomic_positions"),
        )

    def actual_qexsd_path(self) -> Path:
        """Return the configured accepted QE 7.2 QEXSD source path."""
        return self.configured_external_path("KSDFT2EFFMASS_QE72_QEXSD_PATH")

    def actual_qe75_qexsd_path(self) -> Path:
        """Return the configured QE 7.5 smoke-test QEXSD source path."""
        return self.configured_external_path("KSDFT2EFFMASS_QE75_QEXSD_PATH")


QEXSD_FIXTURES = QexsdFixtureResources(Path(__file__).with_name("qexsd"))
CONTROLLED_QEXSD = QEXSD_FIXTURES.controlled_bytes("23.03.10")
CONTROLLED_QEXSD_250521 = QEXSD_FIXTURES.controlled_bytes("25.05.21")
