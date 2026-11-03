r"""Software verification of ``QexsdDocument``.

Evidence profile: routine

Bounded artifact scope: immutable mechanically parsed native QEXSD state.

Facet and represented meaning

The DataObject owns native dimensions, references, finiteness, and cardinalities.

Intrinsic and cross-object scope

Only document-owned invariants and deep tuple immutability are covered.

VVUQ and scientific exclusions

The controlled document establishes no numerical or scientific validity.
"""

from dataclasses import FrozenInstanceError, replace
from typing import Literal

import pytest

from projectkoios.integrations.quantumespresso.qexsd.records import QexsdDocument

from ..resources.qexsd_fixtures import QEXSD_FIXTURES

SUT = QexsdDocument
pytestmark = pytest.mark.software_verification


class TestQexsdDocument:
    """Own this module's maintained software-verification evidence."""

    def test__QexsdDocument__constructor_immutable_state_retains_nested_tuples(
        self,
    ) -> None:
        """Evidence ID: SV-PERIODIC-007

        Requirement: Retained native collections are deeply immutable ordered tuples.

        Acceptance: Nested state is tuple-backed and field reassignment raises
        FrozenInstanceError.
        """
        document = QEXSD_FIXTURES.controlled_document("23.03.10")
        assert type(document.atoms) is tuple and type(document.atoms[0][2]) is tuple
        assert (
            type(document.eigenvalues) is tuple
            and type(document.eigenvalues[0]) is tuple
        )
        with pytest.raises(FrozenInstanceError):
            document.exit_status = 1  # type: ignore[misc]

    @pytest.mark.parametrize(
        "case",
        [
            pytest.param("source_digest", id="source_digest"),
            pytest.param("lattice_shape", id="lattice_shape"),
            pytest.param("atom_cardinality", id="atom_cardinality"),
            pytest.param("species_resolution", id="species_resolution"),
            pytest.param("kpoint_weight_cardinality", id="kpoint_weight_cardinality"),
            pytest.param("spectrum_cardinality", id="spectrum_cardinality"),
            pytest.param("occupation_shape", id="occupation_shape"),
            pytest.param("fft_shape", id="fft_shape"),
            pytest.param("exit_status", id="exit_status"),
        ],
    )
    def test__QexsdDocument__constructor_intrinsic_relationships_rejects_invalid_state(
        self,
        case: Literal[
            "source_digest",
            "lattice_shape",
            "atom_cardinality",
            "species_resolution",
            "kpoint_weight_cardinality",
            "spectrum_cardinality",
            "occupation_shape",
            "fft_shape",
            "exit_status",
        ],
    ) -> None:
        """Evidence ID: SV-PERIODIC-008

        Requirement: Native vector, reference, count, spectrum, grid, and status
        invariants hold.

        Acceptance: Every named invalid replacement raises TypeError or ValueError.
        """
        document = QEXSD_FIXTURES.controlled_document("23.03.10")
        with pytest.raises((TypeError, ValueError)):
            match case:
                case "source_digest":
                    replace(document, source_sha256="bad")
                case "lattice_shape":
                    replace(
                        document,
                        direct_lattice_vectors=((1.0, 0.0),),  # type: ignore[arg-type]
                    )
                case "atom_cardinality":
                    replace(document, declared_atom_count=3)
                case "species_resolution":
                    replace(document, atoms=((1, "Ge", (0.0, 0.0, 0.0)),))
                case "kpoint_weight_cardinality":
                    replace(document, k_point_weights=(1.0,))
                case "spectrum_cardinality":
                    replace(document, eigenvalues=((1.0, 2.0),))
                case "occupation_shape":
                    replace(document, occupations=((1.0,), (1.0, 0.0)))
                case "fft_shape":
                    replace(document, fft_grid=(4, 0, 6))
                case "exit_status":
                    replace(document, exit_status=256)

    @pytest.mark.parametrize(
        "case",
        [
            pytest.param("boolean_byte_count", id="boolean_byte_count"),
            pytest.param("numeric_version", id="numeric_version"),
            pytest.param("boolean_atom_count", id="boolean_atom_count"),
            pytest.param("list_species", id="list_species"),
            pytest.param("boolean_kpoint_count", id="boolean_kpoint_count"),
            pytest.param("boolean_weights", id="boolean_weights"),
            pytest.param("boolean_band_count", id="boolean_band_count"),
            pytest.param("string_energy", id="string_energy"),
            pytest.param("boolean_fft_value", id="boolean_fft_value"),
            pytest.param("boolean_exit_status", id="boolean_exit_status"),
        ],
    )
    def test__QexsdDocument__constructor_semantic_types_raise_type_error(
        self,
        case: Literal[
            "boolean_byte_count",
            "numeric_version",
            "boolean_atom_count",
            "list_species",
            "boolean_kpoint_count",
            "boolean_weights",
            "boolean_band_count",
            "string_energy",
            "boolean_fft_value",
            "boolean_exit_status",
        ],
    ) -> None:
        """Evidence ID: SV-QEXSD-004

        Requirement: Wrong semantic scalar, container, and member types are rejected
        without implicit conversion.

        Acceptance: Every named wrong-type partition raises ``TypeError`` exactly.
        """
        document = QEXSD_FIXTURES.controlled_document("23.03.10")
        with pytest.raises(TypeError):
            match case:
                case "boolean_byte_count":
                    replace(document, source_byte_count=True)
                case "numeric_version":
                    replace(
                        document,
                        producing_application_version=7,  # type: ignore[arg-type]
                    )
                case "boolean_atom_count":
                    replace(document, declared_atom_count=True)
                case "list_species":
                    replace(
                        document,
                        species=(["Si", 28.0, "Si.upf"],),  # type: ignore[arg-type]
                    )
                case "boolean_kpoint_count":
                    replace(document, sampled_k_point_count=True)
                case "boolean_weights":
                    replace(document, k_point_weights=(True, True))
                case "boolean_band_count":
                    replace(document, band_count=True)
                case "string_energy":
                    replace(document, total_energy="-1.0")  # type: ignore[arg-type]
                case "boolean_fft_value":
                    replace(document, fft_grid=(4, True, 6))
                case "boolean_exit_status":
                    replace(document, exit_status=True)

    @pytest.mark.parametrize(
        "case",
        [
            pytest.param("negative_byte_count", id="negative_byte_count"),
            pytest.param("empty_version", id="empty_version"),
            pytest.param("nonfinite_alat", id="nonfinite_alat"),
            pytest.param("zero_atom_count", id="zero_atom_count"),
            pytest.param("zero_kpoint_count", id="zero_kpoint_count"),
            pytest.param("zero_band_count", id="zero_band_count"),
            pytest.param("nonfinite_energy", id="nonfinite_energy"),
            pytest.param("nonpositive_fft_value", id="nonpositive_fft_value"),
            pytest.param("out_of_range_exit_status", id="out_of_range_exit_status"),
        ],
    )
    def test__QexsdDocument__constructor_typed_invariants_raise_value_error(
        self,
        case: Literal[
            "negative_byte_count",
            "empty_version",
            "nonfinite_alat",
            "zero_atom_count",
            "zero_kpoint_count",
            "zero_band_count",
            "nonfinite_energy",
            "nonpositive_fft_value",
            "out_of_range_exit_status",
        ],
    ) -> None:
        """Evidence ID: SV-QEXSD-005

        Requirement: Correctly typed values violating native record invariants are
        rejected without changing represented semantics.

        Acceptance: Every named invalid-value partition raises ``ValueError`` exactly.
        """
        document = QEXSD_FIXTURES.controlled_document("23.03.10")
        with pytest.raises(ValueError):
            match case:
                case "negative_byte_count":
                    replace(document, source_byte_count=-1)
                case "empty_version":
                    replace(document, producing_application_version="")
                case "nonfinite_alat":
                    replace(document, atomic_structure_alat=float("nan"))
                case "zero_atom_count":
                    replace(document, declared_atom_count=0)
                case "zero_kpoint_count":
                    replace(document, sampled_k_point_count=0)
                case "zero_band_count":
                    replace(document, band_count=0)
                case "nonfinite_energy":
                    replace(document, total_energy=float("inf"))
                case "nonpositive_fft_value":
                    replace(document, fft_grid=(4, 0, 6))
                case "out_of_range_exit_status":
                    replace(document, exit_status=256)
