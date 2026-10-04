from __future__ import annotations

import hashlib
import struct

import numpy as np
import pytest

from projectkoios.integrations.quantumespresso.pw2wannier90.provider import (
    QeWannier90ProviderArtifact,
    QeWannier90ProviderArtifactRole,
)
from projectkoios.integrations.quantumespresso.pw2wannier90.unk import (
    QeUnkByteOrder,
    QeWannier90UnkData,
    QeWannier90UnkParser,
)


def _record(payload: bytes, prefix: str) -> bytes:
    marker = struct.pack(f"{prefix}i", len(payload))
    return marker + payload + marker


def _payload(
    *,
    prefix: str = "<",
    basename: str = "UNK00001.1",
    band_count: int = 2,
) -> bytes:
    grid = (2, 2, 1)
    header = _record(struct.pack(f"{prefix}5i", *grid, 1, band_count), prefix)
    spinor_count = 2 if basename.endswith(".NC") else 1
    records = []
    for record_index in range(band_count * spinor_count):
        values = np.asarray(
            [complex(10 * record_index + index, -index) for index in range(4)],
            dtype=np.dtype(f"{prefix}c16"),
        )
        records.append(_record(values.tobytes(), prefix))
    return header + b"".join(records)


def _artifact(
    payload: bytes, basename: str = "UNK00001.1"
) -> QeWannier90ProviderArtifact:
    spin = None if basename.endswith(".NC") else int(basename.rsplit(".", 1)[1])
    return QeWannier90ProviderArtifact(
        role=QeWannier90ProviderArtifactRole.unk,
        relative_path=f"work/qe/{basename}",
        sha256=hashlib.sha256(payload).hexdigest(),
        byte_size=len(payload),
        kpoint_index=1,
        spin_channel_index=spin,
    )


def test_unk_data_cannot_be_constructed_without_authenticated_parser() -> None:
    with pytest.raises(TypeError):
        QeWannier90UnkData()


@pytest.mark.parametrize(
    ("prefix", "expected_order"),
    [("<", QeUnkByteOrder.little_endian), (">", QeUnkByteOrder.big_endian)],
)
def test_decodes_authenticated_native_order(
    prefix: str, expected_order: QeUnkByteOrder
) -> None:
    payload = _payload(prefix=prefix)

    parsed = QeWannier90UnkParser().execute(
        _artifact(payload),
        payload,
        expected_grid_shape=(2, 2, 1),
        expected_band_count=2,
        expected_spinor_component_count=1,
    )

    assert parsed.byte_order is expected_order
    assert parsed.values.shape == (2, 1, 2, 2, 1)
    assert parsed.values[0, 0, 0, 0, 0] == 0.0 + 0.0j
    assert parsed.values[0, 0, 1, 0, 0] == 1.0 - 1.0j
    assert parsed.values[0, 0, 0, 1, 0] == 2.0 - 2.0j
    assert not parsed.values.flags.writeable


def test_decodes_two_component_noncollinear_records() -> None:
    basename = "UNK00001.NC"
    payload = _payload(basename=basename, band_count=1)

    parsed = QeWannier90UnkParser().execute(
        _artifact(payload, basename),
        payload,
        expected_spinor_component_count=2,
    )

    assert parsed.values.shape == (1, 2, 2, 2, 1)
    assert parsed.values[0, 1, 0, 0, 0] == 10.0 + 0.0j


def test_authenticates_before_decoding() -> None:
    payload = _payload()
    wrong = QeWannier90ProviderArtifact(
        role=QeWannier90ProviderArtifactRole.unk,
        relative_path="work/qe/UNK00001.1",
        sha256="0" * 64,
        byte_size=len(payload),
        kpoint_index=1,
        spin_channel_index=1,
    )

    with pytest.raises(ValueError, match="SHA-256"):
        QeWannier90UnkParser().execute(wrong, payload)


def test_rejects_inconsistent_record_marker() -> None:
    payload = bytearray(_payload(band_count=1))
    payload[-1] ^= 1
    malformed = bytes(payload)

    with pytest.raises(ValueError, match="markers disagree"):
        QeWannier90UnkParser().execute(_artifact(malformed), malformed)


def test_rejects_hostile_dimensions_before_decoded_allocation() -> None:
    header = _record(
        struct.pack("<5i", 256, 256, 256, 1, 100_000),
        "<",
    )

    with pytest.raises(ValueError, match="parser byte bound"):
        QeWannier90UnkParser().execute(_artifact(header), header)


def test_rejects_authenticated_trailing_bytes() -> None:
    payload = _payload(band_count=1) + b"trailing"

    with pytest.raises(ValueError, match="trailing bytes"):
        QeWannier90UnkParser().execute(_artifact(payload), payload)
