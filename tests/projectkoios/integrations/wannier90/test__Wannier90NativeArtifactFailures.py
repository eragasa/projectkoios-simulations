"""Failure, correlation, and cross-artifact tests for the parser bundle."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from projectkoios.integrations.wannier90 import (
    Wannier90EigenvalueParser,
    Wannier90HamiltonianBlockParser,
    Wannier90LocalizationParser,
    Wannier90NativeArtifact,
    Wannier90NativeArtifactCorrelator,
    Wannier90NativeArtifactIdentity,
    Wannier90NativeArtifactSetParser,
    Wannier90NeighborListParser,
    Wannier90NeighborOverlapParser,
    Wannier90ProjectionParser,
    Wannier90UnitaryMatrixParser,
)
from projectkoios.physkit.units.quantities import PhysicalUnit

pytestmark = pytest.mark.software_verification

ENERGY_UNIT = PhysicalUnit("electron_volt")
LENGTH_UNIT = PhysicalUnit("angstrom")


def _valid_artifacts() -> tuple[Wannier90NativeArtifact, ...]:
    """Return one minimal internally consistent seven-artifact inventory."""
    payloads = {
        "tiny.eig": b"1 1 -0.0d0\n2 1 2.5D-1\n1 2 +1.25E-2\n2 2 -4.0E+0\n",
        "tiny.amn": (
            b"fixture\n2 2 1\n"
            b"2 1 2 4.0 -4.0\n1 1 1 1.0 -1.0\n"
            b"2 1 1 2.0 -2.0\n1 1 2 3.0 -3.0\n"
        ),
        "tiny.mmn": (
            b"fixture\n2 2 1\n"
            b"1 2 0 0 0\n1.0 0.0\n2.0 0.0\n3.0 0.0\n4.0 0.0\n"
            b"2 1 1 -1 0\n5.0 0.0\n6.0 0.0\n7.0 0.0\n8.0 0.0\n"
        ),
        "tiny.nnkp": (b"begin nnkpts\n1\n1 2 0 0 0\n2 1 1 -1 0\nend nnkpts\n"),
        "tiny.wout": (
            b"Length Unit : Ang\nCycle: 3\n"
            b"WF centre and spread 1 ( 0.0, 0.0, 0.0 ) 0.4\n"
            b"  3  0.0 <-- CONV\nCycle: 7\n"
            b"WF centre and spread 1 ( 0.0, 0.0, 0.0 ) 0.3\n"
            b"  7  0.0 <-- CONV\nFinal State\n"
            b"WF centre and spread 1 ( -0.0, +1.25D-2, 2.0 ) 3.0e-1\n"
            b"Omega I = 0.1\nOmega D = 0.2\nOmega OD = 0.3\n"
            b"Omega Total = 0.6\n"
        ),
        "tiny_u.mat": (
            b"fixture\n2 1 1\n\n0.0 0.0 0.0\n1.0 0.0\n\n0.5 -0.5 +1.25D-2\n3.0 0.0\n"
        ),
        "tiny_hr.dat": (b"fixture\n1\n1\n1\n0 0 0 1 1 -1.25E-2 +0.0\n"),
    }
    return tuple(
        Wannier90NativeArtifact(name, payload) for name, payload in payloads.items()
    )


def test_correlation_rejects_hash_mismatch_with_exact_name_and_size() -> None:
    artifact = Wannier90NativeArtifact("tiny.eig", b"abc")
    wrong = Wannier90NativeArtifactIdentity("tiny.eig", 3, "0" * 64)

    with pytest.raises(ValueError, match="identities do not agree exactly"):
        Wannier90NativeArtifactCorrelator().execute((wrong,), (artifact,))


def test_correlation_rejects_name_inventory_mismatch() -> None:
    expected_artifact = Wannier90NativeArtifact("tiny.eig", b"abc")
    supplied_artifact = Wannier90NativeArtifact("other.eig", b"abc")

    with pytest.raises(ValueError, match="name inventory"):
        Wannier90NativeArtifactCorrelator().execute(
            (expected_artifact.identity,), (supplied_artifact,)
        )


def test_artifact_name_rejects_paths() -> None:
    with pytest.raises(ValueError, match="must not contain a path"):
        Wannier90NativeArtifact("directory/tiny.eig", b"")


def test_set_parser_preserves_units_ordering_and_awkward_numbers() -> None:
    artifacts = _valid_artifacts()
    expected = tuple(artifact.identity for artifact in artifacts)
    correlation = Wannier90NativeArtifactCorrelator().execute(
        expected, tuple(reversed(artifacts))
    )

    parsed = Wannier90NativeArtifactSetParser().execute(
        "tiny", artifacts, ENERGY_UNIT, LENGTH_UNIT
    )

    assert correlation.observed_identities == expected
    assert parsed.eigenvalues.eigenvalues.unit == ENERGY_UNIT
    assert parsed.localization.centers.unit == LENGTH_UNIT
    assert np.signbit(parsed.eigenvalues.eigenvalues.magnitude[0, 0])
    assert parsed.eigenvalues.eigenvalues.magnitude[1, 0] == 1.25e-2
    assert parsed.neighbor_list.records == (
        (1, 2, 0, 0, 0),
        (2, 1, 1, -1, 0),
    )
    assert parsed.neighbor_overlaps.matrices[0].magnitude.tolist() == [
        [(1 + 0j), (3 + 0j)],
        [(2 + 0j), (4 + 0j)],
    ]
    assert parsed.unitary_matrices.matrices[0].magnitude.tolist() == [[(1 + 0j)]]
    assert parsed.hamiltonian_blocks.blocks[0].magnitude[0, 0] == -1.25e-2 + 0j


def test_set_parser_rejects_missing_exact_native_name() -> None:
    artifacts = tuple(
        artifact for artifact in _valid_artifacts() if artifact.name != "tiny.mmn"
    )

    with pytest.raises(
        ValueError, match="required native artifact is absent: tiny.mmn"
    ):
        Wannier90NativeArtifactSetParser().execute(
            "tiny", artifacts, ENERGY_UNIT, LENGTH_UNIT
        )


def test_parsed_set_rejects_cross_artifact_kpoint_count_mismatch() -> None:
    artifacts = _valid_artifacts()
    parsed = Wannier90NativeArtifactSetParser().execute(
        "tiny", artifacts, ENERGY_UNIT, LENGTH_UNIT
    )
    one_kpoint_projection = Wannier90ProjectionParser().execute(
        b"fixture\n2 1 1\n1 1 1 1.0 0.0\n2 1 1 2.0 0.0\n"
    )

    with pytest.raises(ValueError, match="agree on k-point count"):
        replace(parsed, projections=one_kpoint_projection)


def test_parsed_set_rejects_cross_artifact_band_count_mismatch() -> None:
    artifacts = _valid_artifacts()
    parsed = Wannier90NativeArtifactSetParser().execute(
        "tiny", artifacts, ENERGY_UNIT, LENGTH_UNIT
    )
    one_band_eigenvalues = Wannier90EigenvalueParser().execute(
        b"1 1 1.0\n1 2 2.0\n", ENERGY_UNIT
    )

    with pytest.raises(ValueError, match="agree on band count"):
        replace(parsed, eigenvalues=one_band_eigenvalues)


def test_parsed_set_rejects_cross_artifact_wannier_count_mismatch() -> None:
    artifacts = _valid_artifacts()
    parsed = Wannier90NativeArtifactSetParser().execute(
        "tiny", artifacts, ENERGY_UNIT, LENGTH_UNIT
    )
    two_wannier_localization = Wannier90LocalizationParser().execute(
        b"Length Unit : Ang\nCycle: 1\n"
        b"WF centre and spread 1 ( 0, 0, 0 ) 0.1\n"
        b"WF centre and spread 2 ( 0, 0, 0 ) 0.2\n"
        b"1 0.0 <-- CONV\nFinal State\n"
        b"WF centre and spread 1 ( 0, 0, 0 ) 0.1\n"
        b"WF centre and spread 2 ( 0, 0, 0 ) 0.2\n"
        b"Omega I = 0.1\nOmega D = 0.2\nOmega OD = 0.3\nOmega Total = 0.6\n",
        LENGTH_UNIT,
    )

    with pytest.raises(ValueError, match="agree on Wannier count"):
        replace(parsed, localization=two_wannier_localization)


@pytest.mark.parametrize(
    ("parser", "payload", "arguments", "message"),
    [
        (
            Wannier90EigenvalueParser(),
            b"1 1 0.0\n2 2 1.0\n",
            (ENERGY_UNIT,),
            "complete table",
        ),
        (
            Wannier90ProjectionParser(),
            b"fixture\n1 1 1\n",
            (),
            "complete table",
        ),
        (
            Wannier90NeighborListParser(),
            b"begin nnkpts\n2\n1 1 0 0 0\nend nnkpts\n",
            (),
            "divisible",
        ),
    ],
)
def test_count_mismatches_are_rejected(
    parser: object, payload: bytes, arguments: tuple[object, ...], message: str
) -> None:
    execute = parser.execute
    with pytest.raises(ValueError, match=message):
        execute(payload, *arguments)


@pytest.mark.parametrize(
    ("parser", "payload", "arguments", "message"),
    [
        (
            Wannier90NeighborOverlapParser(),
            b"fixture\n1 1 1\n1 1 0 0 0\n",
            (),
            "ends within a matrix",
        ),
        (
            Wannier90UnitaryMatrixParser(),
            b"fixture\n1 1 1\n0 0 0\n",
            (),
            "ends within a matrix",
        ),
        (
            Wannier90HamiltonianBlockParser(),
            b"fixture\n1\n1\n1\n",
            (ENERGY_UNIT,),
            "ends within a Hamiltonian block",
        ),
    ],
)
def test_truncated_matrix_payloads_are_rejected(
    parser: object, payload: bytes, arguments: tuple[object, ...], message: str
) -> None:
    execute = parser.execute
    with pytest.raises(ValueError, match=message):
        execute(payload, *arguments)


@pytest.mark.parametrize(
    ("parser", "arguments"),
    [
        (Wannier90EigenvalueParser(), (ENERGY_UNIT,)),
        (Wannier90ProjectionParser(), ()),
        (Wannier90NeighborOverlapParser(), ()),
        (Wannier90NeighborListParser(), ()),
        (Wannier90LocalizationParser(), (LENGTH_UNIT,)),
        (Wannier90UnitaryMatrixParser(), ()),
        (Wannier90HamiltonianBlockParser(), (ENERGY_UNIT,)),
    ],
)
def test_every_parser_rejects_non_utf8(
    parser: object, arguments: tuple[object, ...]
) -> None:
    execute = parser.execute
    with pytest.raises(ValueError, match="valid UTF-8"):
        execute(b"\xff", *arguments)
