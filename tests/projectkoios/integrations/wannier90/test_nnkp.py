from __future__ import annotations

import pytest

from projectkoios.integrations.wannier90 import (
    Wannier90NnkpParser,
    Wannier90ParserLimits,
)


def _payload(*, excluded_count: str = "1\n2") -> bytes:
    return f"""generated interface
calc_only_A : F
begin real_lattice
1.0 0.0 0.0
0.0 1.0 0.0
0.0 0.0 1.0
end real_lattice
begin recip_lattice
6.0 0.0 0.0
0.0 6.0 0.0
0.0 0.0 6.0
end recip_lattice
begin kpoints
2
0.0 0.0 0.0
0.5 0.0 0.0
end kpoints
begin projections
1
0.0 0.0 0.0 0 1 1
0.0 0.0 1.0 1.0 0.0 0.0 1.0
end projections
begin nnkpts
1
1 2 0 0 0
2 1 1 0 0
end nnkpts
begin exclude_bands
{excluded_count}
end exclude_bands
""".encode("ascii")


def test_parses_complete_generated_coordinate_and_neighbor_contract() -> None:
    parsed = Wannier90NnkpParser().execute(_payload())

    assert parsed.real_lattice[0] == (1.0, 0.0, 0.0)
    assert parsed.reciprocal_lattice[2] == (0.0, 0.0, 6.0)
    assert parsed.kpoints == ((0.0, 0.0, 0.0), (0.5, 0.0, 0.0))
    assert parsed.projections[0].magnetic_index == 1
    assert parsed.neighbor_count == 1
    assert parsed.neighbors[1].reciprocal_cell_shift == (1, 0, 0)
    assert parsed.excluded_bands == (2,)


def test_rejects_missing_declared_excluded_band() -> None:
    with pytest.raises(ValueError, match="declared count disagrees"):
        Wannier90NnkpParser().execute(_payload(excluded_count="1"))


def test_honors_aggregate_neighbor_record_limit() -> None:
    limits = Wannier90ParserLimits(maximum_records=2)
    payload = _payload().replace(
        b"begin nnkpts\n1\n1 2 0 0 0\n2 1 1 0 0\nend nnkpts",
        b"begin nnkpts\n2\n1 2 0 0 0\n1 1 0 0 0\n2 1 1 0 0\n2 2 0 0 0\nend nnkpts",
    )

    with pytest.raises(ValueError, match="maximum_records"):
        Wannier90NnkpParser(limits).execute(payload)


def test_rejects_unmatched_section_terminator() -> None:
    payload = _payload() + b"end stray\n"

    with pytest.raises(ValueError, match="unmatched NNKP section terminator"):
        Wannier90NnkpParser().execute(payload)


def test_rejects_unknown_generated_section() -> None:
    payload = _payload().replace(
        b"begin projections", b"begin unsupported\nend unsupported\nbegin projections"
    )

    with pytest.raises(ValueError, match="unsupported NNKP section"):
        Wannier90NnkpParser().execute(payload)
