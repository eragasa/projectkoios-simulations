"""Adversarial native-format and resource-bound parser regressions."""

from __future__ import annotations

from dataclasses import replace

import pytest
from physkit.units.quantities import PhysicalUnit

from projectkoios.integrations.wannier90 import (
    Wannier90EigenvalueParser,
    Wannier90HamiltonianBlockParser,
    Wannier90LocalizationParser,
    Wannier90NativeArtifact,
    Wannier90NativeArtifactSetParser,
    Wannier90NeighborListParser,
    Wannier90NeighborOverlapParser,
    Wannier90ParserLimits,
    Wannier90ProjectionParser,
    Wannier90UnitaryMatrixParser,
)

pytestmark = pytest.mark.software_verification
ENERGY = PhysicalUnit("electron_volt")
LENGTH = PhysicalUnit("angstrom")


def _wout(*, unit: str = "Ang", final_indices: tuple[int, ...] = (1,)) -> bytes:
    final = "\n".join(
        f"WF centre and spread {index} ( 0.0, 0.0, 0.0 ) 0.1" for index in final_indices
    )
    return (
        f"| Length Unit : {unit} |\r\n"
        "Initial State\r\n"
        "WF centre and spread 1 ( 0.0D0, 0.0d0, 0.0E0 ) 0.1D0\r\n"
        "0 0.0D0 <-- CONV\r\n"
        "Final State\r\n"
        f"{final}\r\n"
        "Omega I = 0.1D0\r\n"
        "Omega D = 0.2d0\r\n"
        "Omega OD = 0.3E0\r\n"
        "Omega Total = 0.6e0\r\n"
    ).encode()


def _artifact_set() -> tuple[Wannier90NativeArtifact, ...]:
    payloads = {
        "case.eig": b"1 1 1.0D0\n2 1 2.0d0\n",
        "case.amn": (
            b"case\n2 1 3\n"
            b"1 1 1 1.0D0 0.0\n2 1 1 0.0 0.0\n"
            b"1 2 1 0.0 0.0\n2 2 1 1.0d0 0.0\n"
            b"1 3 1 0.5E0 0.0\n2 3 1 0.0 0.5e0\n"
        ),
        "case.mmn": (
            b"case\n2 1 1\n1 1 1 0 0\n1.0D0 0.0\n0.0 0.0\n0.0 0.0\n1.0d0 0.0\n"
        ),
        "case.nnkp": b"begin nnkpts\n1\n1 1 1 0 0\nend nnkpts\n",
        "case.wout": _wout(),
        "case_u.mat": b"case\n1 1 1\n0.0D0 0.0 0.0\n1.0d0 0.0\n",
        "case_hr.dat": b"case\n1\n1\n1\n0 0 0 1 1 1.0D0 0.0\n",
    }
    return tuple(
        Wannier90NativeArtifact(name, payload) for name, payload in payloads.items()
    )


def test_native_u_matrix_is_square_and_independent_of_band_count() -> None:
    parsed = Wannier90NativeArtifactSetParser().execute(
        "case", _artifact_set(), ENERGY, LENGTH
    )

    assert parsed.eigenvalues.band_count == 2
    assert parsed.projections.projection_count == 3
    assert parsed.unitary_matrices.wannier_count == 1

    with pytest.raises(ValueError, match="rectangular _u_dis.mat is unsupported"):
        Wannier90UnitaryMatrixParser().execute(b"case\n1 2 1\n0 0 0\n1 0\n2 0\n")


def test_eigenvalue_native_order_is_not_silently_sorted() -> None:
    with pytest.raises(ValueError, match="native band/k-point order"):
        Wannier90EigenvalueParser().execute(b"2 1 2.0\n1 1 1.0\n", ENERGY)


def test_nnkp_rejects_out_of_range_duplicate_and_non_normalized_records() -> None:
    with pytest.raises(ValueError, match="target k-point index"):
        Wannier90NeighborListParser().execute(
            b"begin nnkpts\n1\n1 3 0 0 0\n2 1 0 0 0\nend nnkpts\n"
        )
    with pytest.raises(ValueError, match="duplicate record"):
        Wannier90NeighborListParser().execute(
            b"begin nnkpts\n2\n1 1 0 0 0\n1 1 0 0 0\nend nnkpts\n"
        )
    with pytest.raises(ValueError, match="normalized native order"):
        Wannier90NeighborListParser().execute(
            b"begin nnkpts\n1\n2 1 0 0 0\n1 2 0 0 0\nend nnkpts\n"
        )


@pytest.mark.parametrize(
    "nnkp",
    [
        b"begin nnkpts\n1\n1 1 0 0 0\nend nnkpts\n",
        b"begin nnkpts\n2\n1 1 1 0 0\n1 1 0 0 0\nend nnkpts\n",
    ],
)
def test_set_correlation_rejects_mmn_neighbor_count_or_shift(nnkp: bytes) -> None:
    artifacts = tuple(
        replace(artifact, payload=nnkp) if artifact.name == "case.nnkp" else artifact
        for artifact in _artifact_set()
    )

    with pytest.raises(ValueError, match="nnkp and mmn"):
        Wannier90NativeArtifactSetParser().execute("case", artifacts, ENERGY, LENGTH)


def test_mmn_rejects_out_of_range_target_before_returning_data() -> None:
    with pytest.raises(ValueError, match="outside declared count"):
        Wannier90NeighborOverlapParser().execute(b"case\n1 1 1\n1 2 0 0 0\n1.0 0.0\n")


def test_wout_normalizes_crlf_and_retains_validated_source_unit() -> None:
    parsed = Wannier90LocalizationParser().execute(_wout(), LENGTH)

    assert parsed.source_length_unit_label == "Ang"
    assert parsed.reported_wannierisation_iterations == (0,)
    assert parsed.last_reported_wannierisation_iteration == 0


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (_wout(unit="Bohr"), "contradicts"),
        (_wout(final_indices=(2, 1)), "ordered, unique, and one-based"),
        (
            _wout().replace(b"Omega I =", b"Omega IOD ="),
            "selective-localization Omega variants",
        ),
    ],
)
def test_wout_rejects_unit_index_and_selective_omega_contradictions(
    payload: bytes, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        Wannier90LocalizationParser().execute(payload, LENGTH)


def test_wout_rejects_duplicate_iteration_wf_indices() -> None:
    payload = _wout().replace(
        b"0 0.0D0 <-- CONV",
        b"WF centre and spread 1 ( 0, 0, 0 ) 0.1\r\n0 0.0D0 <-- CONV",
    )
    with pytest.raises(ValueError, match="ordered, unique, and one-based"):
        Wannier90LocalizationParser().execute(payload, LENGTH)


def test_wout_rejects_iteration_and_final_state_wf_inventory_mismatch() -> None:
    payload = _wout(final_indices=(1, 2))

    with pytest.raises(ValueError, match="inventories do not agree"):
        Wannier90LocalizationParser().execute(payload, LENGTH)


@pytest.mark.parametrize(
    ("parser", "payload", "arguments"),
    [
        (Wannier90EigenvalueParser(), b"1 1 nan\n", (ENERGY,)),
        (Wannier90ProjectionParser(), b"x\n1 1 1\n1 1 1 inf 0\n", ()),
        (
            Wannier90NeighborOverlapParser(),
            b"x\n1 1 1\n1 1 0 0 0\n-nan 0\n",
            (),
        ),
        (Wannier90UnitaryMatrixParser(), b"x\n1 1 1\n0 0 inf\n1 0\n", ()),
        (
            Wannier90HamiltonianBlockParser(),
            b"x\n1\n1\n1\n0 0 0 1 1 1 nan\n",
            (ENERGY,),
        ),
    ],
)
def test_all_native_numeric_parsers_reject_nonfinite_tokens(
    parser: object, payload: bytes, arguments: tuple[object, ...]
) -> None:
    with pytest.raises(ValueError, match="finite Fortran real"):
        parser.execute(payload, *arguments)


@pytest.mark.parametrize(
    ("parser", "payload", "arguments"),
    [
        (
            Wannier90EigenvalueParser(),
            b"1 1 0\n1000000000 1000000000 0\n",
            (ENERGY,),
        ),
        (Wannier90ProjectionParser(), b"x\n1000000000 1 1\n", ()),
        (Wannier90NeighborOverlapParser(), b"x\n1000000000 1 1\n", ()),
        (Wannier90UnitaryMatrixParser(), b"x\n1 1000000000 1000000000\n", ()),
        (
            Wannier90HamiltonianBlockParser(),
            b"x\n1000000000\n1\n1\n",
            (ENERGY,),
        ),
    ],
)
def test_tiny_huge_headers_are_rejected_before_array_allocation(
    parser: object, payload: bytes, arguments: tuple[object, ...]
) -> None:
    with pytest.raises(ValueError, match="maximum_dimension"):
        parser.execute(payload, *arguments)


def test_configurable_byte_and_checked_product_limits_are_deterministic() -> None:
    limits = Wannier90ParserLimits(
        maximum_payload_bytes=7, maximum_dimension=100, maximum_records=10
    )
    with pytest.raises(ValueError, match="maximum_payload_bytes"):
        Wannier90EigenvalueParser(limits).execute(b"1 1 0.0\n", ENERGY)

    product_limits = Wannier90ParserLimits(
        maximum_payload_bytes=100, maximum_dimension=100, maximum_records=10
    )
    with pytest.raises(ValueError, match="maximum_records"):
        Wannier90ProjectionParser(product_limits).execute(b"x\n3 2 2\n")
