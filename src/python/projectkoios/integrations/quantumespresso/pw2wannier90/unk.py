"""Authenticated decoding of native ``pw2wannier90.x`` UNK files."""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from enum import StrEnum
from typing import Self

import numpy as np
from numpy.typing import NDArray

from projectkoios.integrations.quantumespresso.pw2wannier90.provider import (
    QeWannier90ProviderArtifact,
    QeWannier90ProviderArtifactRole,
)


class QeUnkByteOrder(StrEnum):
    """Byte order authenticated from consistent Fortran record framing."""

    little_endian = "little-endian"
    big_endian = "big-endian"


class QeUnkRecordFraming(StrEnum):
    """Supported native sequential-record representation."""

    signed_32_bit_markers = "fortran-sequential-signed-32-bit-markers"


class QeUnkGridStorageOrder(StrEnum):
    """Native coordinate serialization order within each complex record."""

    first_axis_fastest = "first-axis-fastest-fortran-order"


class QeUnkCoordinateConvention(StrEnum):
    """Meaning of decoded complex values without claiming Hilbert-space norm."""

    qe_periodic_part_real_space_grid = "qe-periodic-part-real-space-grid"


class QeUnkNormalizationConvention(StrEnum):
    """Bounded statement about values written by QE's inverse FFT path.

    ``native_inverse_fft_samples`` deliberately makes no claim that an ordinary
    discrete sum of ``abs(u)**2`` is one. Ultrasoft and PAW calculations require
    their generalized overlap metric, which is not encoded in an UNK file.
    """

    native_inverse_fft_samples = "native-inverse-fft-samples-no-renormalization"


@dataclass(frozen=True, slots=True, eq=False, init=False)
class QeWannier90UnkData:
    """One authenticated UNK decoded into ``(band, spinor, x, y, z)`` order."""

    artifact: QeWannier90ProviderArtifact
    byte_order: QeUnkByteOrder
    record_framing: QeUnkRecordFraming
    grid_storage_order: QeUnkGridStorageOrder
    coordinate_convention: QeUnkCoordinateConvention
    normalization_convention: QeUnkNormalizationConvention
    grid_shape: tuple[int, int, int]
    kpoint_index: int
    band_count: int
    spinor_component_count: int
    values: NDArray[np.complex128]

    def __init__(self) -> None:
        raise TypeError("QeWannier90UnkData must be created by QeWannier90UnkParser")

    @classmethod
    def _from_authenticated(
        cls,
        *,
        artifact: QeWannier90ProviderArtifact,
        byte_order: QeUnkByteOrder,
        record_framing: QeUnkRecordFraming,
        grid_storage_order: QeUnkGridStorageOrder,
        coordinate_convention: QeUnkCoordinateConvention,
        normalization_convention: QeUnkNormalizationConvention,
        grid_shape: tuple[int, int, int],
        kpoint_index: int,
        band_count: int,
        spinor_component_count: int,
        values: NDArray[np.complex128],
    ) -> Self:
        instance = object.__new__(cls)
        fields = {
            "artifact": artifact,
            "byte_order": byte_order,
            "record_framing": record_framing,
            "grid_storage_order": grid_storage_order,
            "coordinate_convention": coordinate_convention,
            "normalization_convention": normalization_convention,
            "grid_shape": grid_shape,
            "kpoint_index": kpoint_index,
            "band_count": band_count,
            "spinor_component_count": spinor_component_count,
            "values": values,
        }
        for name, value in fields.items():
            object.__setattr__(instance, name, value)
        instance.__post_init__()
        return instance

    def __post_init__(self) -> None:
        if type(self.artifact) is not QeWannier90ProviderArtifact:
            raise TypeError("artifact must be a provider artifact")
        if self.artifact.role is not QeWannier90ProviderArtifactRole.unk:
            raise ValueError("artifact role must be UNK")
        if type(self.byte_order) is not QeUnkByteOrder:
            raise TypeError("byte_order has the wrong enum type")
        if type(self.record_framing) is not QeUnkRecordFraming:
            raise TypeError("record_framing has the wrong enum type")
        if type(self.grid_storage_order) is not QeUnkGridStorageOrder:
            raise TypeError("grid_storage_order has the wrong enum type")
        if type(self.coordinate_convention) is not QeUnkCoordinateConvention:
            raise TypeError("coordinate_convention has the wrong enum type")
        if type(self.normalization_convention) is not QeUnkNormalizationConvention:
            raise TypeError("normalization_convention has the wrong enum type")
        if (
            type(self.grid_shape) is not tuple
            or len(self.grid_shape) != 3
            or any(type(value) is not int or value <= 0 for value in self.grid_shape)
        ):
            raise ValueError("grid_shape must contain three positive integers")
        for label, value in (
            ("kpoint_index", self.kpoint_index),
            ("band_count", self.band_count),
            ("spinor_component_count", self.spinor_component_count),
        ):
            if type(value) is not int or value <= 0:
                raise ValueError(f"{label} must be positive")
        if type(
            self.spinor_component_count
        ) is not int or self.spinor_component_count not in {1, 2}:
            raise ValueError("spinor_component_count must be one or two")
        if self.artifact.kpoint_index != self.kpoint_index:
            raise ValueError("artifact and decoded k-point indices disagree")
        if type(self.values) is not np.ndarray:
            raise TypeError("values must be a numpy ndarray")
        expected_shape = (
            self.band_count,
            self.spinor_component_count,
            *self.grid_shape,
        )
        if self.values.dtype != np.dtype(np.complex128):
            raise TypeError("values must have complex128 dtype")
        if self.values.shape != expected_shape:
            raise ValueError("values shape disagrees with decoded dimensions")
        if not np.all(np.isfinite(self.values)):
            raise ValueError("UNK values must be finite")
        self.values.flags.writeable = False

    @property
    def grid_point_count(self) -> int:
        """Return the full real-space FFT-grid point count."""
        return math.prod(self.grid_shape)

    def grid_fractional_coordinate(
        self, index: tuple[int, int, int]
    ) -> tuple[float, float, float]:
        """Map a zero-based native grid index to direct-cell fractional position."""
        if (
            type(index) is not tuple
            or len(index) != 3
            or any(type(value) is not int for value in index)
        ):
            raise TypeError("index must contain three built-in integers")
        if any(
            value < 0 or value >= size
            for value, size in zip(index, self.grid_shape, strict=True)
        ):
            raise IndexError("grid index is out of range")
        return (
            index[0] / self.grid_shape[0],
            index[1] / self.grid_shape[1],
            index[2] / self.grid_shape[2],
        )


@dataclass(frozen=True, slots=True)
class QeWannier90UnkParser:
    """Decode exact authenticated UNK bytes with bounded allocation."""

    max_grid_points: int = 256 * 256 * 256
    max_band_count: int = 100_000
    max_byte_size: int = 16 * 1024 * 1024 * 1024

    def __post_init__(self) -> None:
        for label, value in (
            ("max_grid_points", self.max_grid_points),
            ("max_band_count", self.max_band_count),
            ("max_byte_size", self.max_byte_size),
        ):
            if type(value) is not int or value <= 0:
                raise ValueError(f"{label} must be positive")

    def execute(
        self,
        artifact: QeWannier90ProviderArtifact,
        payload: bytes,
        *,
        expected_grid_shape: tuple[int, int, int] | None = None,
        expected_band_count: int | None = None,
        expected_spinor_component_count: int | None = None,
    ) -> QeWannier90UnkData:
        """Authenticate before decoding and reject every unconsumed byte."""
        if type(artifact) is not QeWannier90ProviderArtifact:
            raise TypeError("artifact must be a provider artifact")
        if artifact.role is not QeWannier90ProviderArtifactRole.unk:
            raise ValueError("artifact role must be UNK")
        if artifact.byte_size > self.max_byte_size:
            raise ValueError("UNK byte size exceeds parser bound")
        artifact.authenticate(payload)
        byte_order, prefix = self._detect_byte_order(payload)
        offset = 0
        header, offset = self._record(payload, offset, prefix)
        if len(header) != 20:
            raise ValueError("UNK header record must contain five 32-bit integers")
        nx, ny, nz, kpoint_index, band_count = struct.unpack(f"{prefix}5i", header)
        grid_shape = (nx, ny, nz)
        if any(value <= 0 for value in grid_shape):
            raise ValueError("UNK grid dimensions must be positive")
        grid_points = math.prod(grid_shape)
        if grid_points > self.max_grid_points:
            raise ValueError("UNK grid exceeds parser bound")
        if band_count <= 0 or band_count > self.max_band_count:
            raise ValueError("UNK band count is outside parser bounds")
        if kpoint_index != artifact.kpoint_index:
            raise ValueError("UNK header and artifact k-point indices disagree")
        if expected_grid_shape is not None and grid_shape != expected_grid_shape:
            raise ValueError("UNK grid disagrees with the expected FFT grid")
        if expected_band_count is not None and band_count != expected_band_count:
            raise ValueError("UNK band count disagrees with the expected band count")
        spinor_component_count = 2 if artifact.basename.endswith(".NC") else 1
        if (
            expected_spinor_component_count is not None
            and spinor_component_count != expected_spinor_component_count
        ):
            raise ValueError("UNK spinor count disagrees with the expected frame")
        record_byte_size = grid_points * np.dtype(np.complex128).itemsize
        record_count = band_count * spinor_component_count
        expected_byte_size = offset + record_count * (record_byte_size + 8)
        if expected_byte_size > self.max_byte_size:
            raise ValueError("decoded UNK dimensions exceed the parser byte bound")
        if len(payload) < expected_byte_size:
            raise ValueError("UNK payload is truncated for its declared dimensions")
        if len(payload) > expected_byte_size:
            raise ValueError("unexpected trailing bytes after UNK records")
        values = np.empty(
            (band_count, spinor_component_count, nx, ny, nz),
            dtype=np.complex128,
        )
        disk_dtype = np.dtype(f"{prefix}c16")
        for band_index in range(band_count):
            for spinor_index in range(spinor_component_count):
                record, offset = self._record(payload, offset, prefix)
                if len(record) != record_byte_size:
                    raise ValueError("UNK complex record size disagrees with its grid")
                flat = np.frombuffer(record, dtype=disk_dtype)
                values[band_index, spinor_index] = flat.reshape(
                    grid_shape, order="F"
                ).astype(np.complex128, copy=False)
        if offset != len(payload):
            raise ValueError("unexpected trailing bytes after UNK records")
        return QeWannier90UnkData._from_authenticated(
            artifact=artifact,
            byte_order=byte_order,
            record_framing=QeUnkRecordFraming.signed_32_bit_markers,
            grid_storage_order=QeUnkGridStorageOrder.first_axis_fastest,
            coordinate_convention=QeUnkCoordinateConvention.qe_periodic_part_real_space_grid,
            normalization_convention=QeUnkNormalizationConvention.native_inverse_fft_samples,
            grid_shape=grid_shape,
            kpoint_index=kpoint_index,
            band_count=band_count,
            spinor_component_count=spinor_component_count,
            values=values,
        )

    @staticmethod
    def _detect_byte_order(payload: bytes) -> tuple[QeUnkByteOrder, str]:
        if len(payload) < 28:
            raise ValueError("UNK payload is too short for its header record")
        matches: list[tuple[QeUnkByteOrder, str]] = []
        for byte_order, prefix in (
            (QeUnkByteOrder.little_endian, "<"),
            (QeUnkByteOrder.big_endian, ">"),
        ):
            leading = struct.unpack_from(f"{prefix}i", payload, 0)[0]
            trailing = struct.unpack_from(f"{prefix}i", payload, 24)[0]
            if leading == 20 and trailing == 20:
                matches.append((byte_order, prefix))
        if len(matches) != 1:
            raise ValueError("UNK byte order or header record framing is invalid")
        return matches[0]

    @staticmethod
    def _record(payload: bytes, offset: int, prefix: str) -> tuple[memoryview, int]:
        if offset + 8 > len(payload):
            raise ValueError("truncated UNK Fortran record")
        size = struct.unpack_from(f"{prefix}i", payload, offset)[0]
        if size < 0:
            raise ValueError("negative or segmented UNK records are unsupported")
        data_start = offset + 4
        data_end = data_start + size
        marker_end = data_end + 4
        if marker_end > len(payload):
            raise ValueError("truncated UNK Fortran record")
        trailing = struct.unpack_from(f"{prefix}i", payload, data_end)[0]
        if trailing != size:
            raise ValueError("UNK Fortran record markers disagree")
        return memoryview(payload)[data_start:data_end], marker_end
