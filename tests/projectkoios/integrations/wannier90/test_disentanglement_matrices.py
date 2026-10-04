from __future__ import annotations

import numpy as np
import pytest

from projectkoios.integrations.wannier90 import (
    Wannier90DisentanglementMatrixParser,
    Wannier90MatrixStorageOrder,
)


def _payload(header: str = "1 2 3", *, trailing: bool = False) -> bytes:
    lines = [
        "synthetic u_dis",
        header,
        "0.0 0.25 0.5",
        "1.0 0.0",
        "2.0 0.0",
        "3.0 0.0",
        "4.0 0.0",
        "5.0 0.0",
        "6.0 0.0",
    ]
    if trailing:
        lines.append("7.0 0.0")
    return ("\n".join(lines) + "\n").encode("ascii")


def test_parses_native_header_and_band_by_wannier_orientation() -> None:
    parsed = Wannier90DisentanglementMatrixParser().execute(_payload())

    assert parsed.kpoint_count == 1
    assert parsed.band_count == 3
    assert parsed.wannier_count == 2
    assert parsed.storage_order is Wannier90MatrixStorageOrder.first_index_fastest
    np.testing.assert_array_equal(
        parsed.matrices[0].magnitude,
        np.asarray([[1.0, 4.0], [2.0, 5.0], [3.0, 6.0]], dtype=np.complex128),
    )


def test_rejects_header_with_more_wanniers_than_bands() -> None:
    with pytest.raises(ValueError, match="must not exceed"):
        Wannier90DisentanglementMatrixParser().execute(_payload("1 4 3"))


def test_rejects_trailing_matrix_entries() -> None:
    with pytest.raises(ValueError, match="trailing records"):
        Wannier90DisentanglementMatrixParser().execute(_payload(trailing=True))
