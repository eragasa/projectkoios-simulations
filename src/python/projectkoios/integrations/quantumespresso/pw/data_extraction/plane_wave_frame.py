"""Authoritative plane-wave frame extracted from the existing QEXSD facade."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, Self, cast

import numpy as np

from projectkoios.integrations.quantumespresso.pseudopotential import (
    QePseudopotentialFile,
)
from projectkoios.integrations.quantumespresso.pw.data_extraction.qexsd import (
    QeQexsdData,
)

_BOHR_TO_ANGSTROM = 0.529177210903
_REQUIRED_FIELDS = (
    "declared_unit_system_label",
    "atomic_structure_alat",
    "direct_lattice_vectors",
    "direct_lattice_source_label",
    "reciprocal_lattice_coefficients",
    "reciprocal_lattice_source_label",
    "species",
    "k_points",
    "k_point_source_label",
    "sampled_k_point_count",
    "band_count",
    "fft_grid",
)

type Vector3 = tuple[float, float, float]
type Matrix3 = tuple[Vector3, Vector3, Vector3]


class QeReciprocalScaleConvention(StrEnum):
    """Native QEXSD reciprocal-vector and k-point scale."""

    two_pi_over_alat_cartesian = "cartesian-coefficients-times-2pi-over-alat"


class QeFftGVectorMapping(StrEnum):
    """QE full-grid indexing with fail-closed even-grid Nyquist handling."""

    first_axis_fastest_signed_fft_non_nyquist = (
        "first-axis-fastest-signed-fft-frequencies-excluding-nyquist"
    )


class QeUnkFourierConvention(StrEnum):
    """Explicit transform paired with QE real-space UNK samples."""

    forward_negative_exponent_divide_by_grid_size = (
        "forward-negative-exponent-divide-by-grid-size"
    )


class QeWavefunctionOverlapMetric(StrEnum):
    """Metric needed to interpret wavefunction normalization."""

    identity = "identity"
    ultrasoft_generalized = "ultrasoft-generalized-overlap"
    paw_generalized = "paw-generalized-overlap"


class _QePseudopotentialFormalism(StrEnum):
    norm_conserving = "norm-conserving"
    ultrasoft = "ultrasoft"
    paw = "paw"


@dataclass(frozen=True, slots=True, init=False)
class QePlaneWaveFrame:
    """QEXSD-backed geometry needed to evaluate ``0.5*|k+G|**2``.

    Vectors are Cartesian. Direct vectors are in bohr; physical reciprocal
    vectors and k-points are in inverse bohr. Reduced k-points are coefficients
    of the three source-ordered reciprocal vectors. No H-minus-T operation is
    implemented here.
    """

    qexsd: QeQexsdData
    pseudopotentials: tuple[QePseudopotentialFile, ...]
    reciprocal_scale_convention: QeReciprocalScaleConvention
    fft_g_vector_mapping: QeFftGVectorMapping
    fourier_convention: QeUnkFourierConvention
    overlap_metric: QeWavefunctionOverlapMetric
    direct_lattice_bohr: Matrix3
    reciprocal_lattice_per_bohr: Matrix3
    kpoints_reduced: tuple[Vector3, ...]
    kpoints_per_bohr: tuple[Vector3, ...]
    fft_grid: tuple[int, int, int]
    band_count: int
    spin_channel_count: int
    spinor_component_count: int

    def __init__(self) -> None:
        raise TypeError("QePlaneWaveFrame must be created by QePlaneWaveFrameExtractor")

    @classmethod
    def _from_extracted(
        cls,
        *,
        qexsd: QeQexsdData,
        pseudopotentials: tuple[QePseudopotentialFile, ...],
        reciprocal_scale_convention: QeReciprocalScaleConvention,
        fft_g_vector_mapping: QeFftGVectorMapping,
        fourier_convention: QeUnkFourierConvention,
        overlap_metric: QeWavefunctionOverlapMetric,
        direct_lattice_bohr: Matrix3,
        reciprocal_lattice_per_bohr: Matrix3,
        kpoints_reduced: tuple[Vector3, ...],
        kpoints_per_bohr: tuple[Vector3, ...],
        fft_grid: tuple[int, int, int],
        band_count: int,
        spin_channel_count: int,
        spinor_component_count: int,
    ) -> Self:
        instance = object.__new__(cls)
        values = {
            "qexsd": qexsd,
            "pseudopotentials": pseudopotentials,
            "reciprocal_scale_convention": reciprocal_scale_convention,
            "fft_g_vector_mapping": fft_g_vector_mapping,
            "fourier_convention": fourier_convention,
            "overlap_metric": overlap_metric,
            "direct_lattice_bohr": direct_lattice_bohr,
            "reciprocal_lattice_per_bohr": reciprocal_lattice_per_bohr,
            "kpoints_reduced": kpoints_reduced,
            "kpoints_per_bohr": kpoints_per_bohr,
            "fft_grid": fft_grid,
            "band_count": band_count,
            "spin_channel_count": spin_channel_count,
            "spinor_component_count": spinor_component_count,
        }
        for name, value in values.items():
            object.__setattr__(instance, name, value)
        instance.__post_init__()
        return instance

    def __post_init__(self) -> None:
        if type(self.qexsd) is not QeQexsdData:
            raise TypeError("qexsd must be QeQexsdData")
        if type(self.pseudopotentials) is not tuple or not self.pseudopotentials:
            raise ValueError("pseudopotentials must be a nonempty tuple")
        if any(
            type(item) is not QePseudopotentialFile for item in self.pseudopotentials
        ):
            raise TypeError(
                "pseudopotentials must contain QePseudopotentialFile values"
            )
        for enum_type, value, label in (
            (
                QeReciprocalScaleConvention,
                self.reciprocal_scale_convention,
                "reciprocal_scale_convention",
            ),
            (QeFftGVectorMapping, self.fft_g_vector_mapping, "fft_g_vector_mapping"),
            (QeUnkFourierConvention, self.fourier_convention, "fourier_convention"),
            (QeWavefunctionOverlapMetric, self.overlap_metric, "overlap_metric"),
        ):
            if type(value) is not enum_type:
                raise TypeError(f"{label} has the wrong enum type")
        _validate_matrix(self.direct_lattice_bohr, "direct_lattice_bohr")
        _validate_matrix(
            self.reciprocal_lattice_per_bohr, "reciprocal_lattice_per_bohr"
        )
        for label, vectors in (
            ("kpoints_reduced", self.kpoints_reduced),
            ("kpoints_per_bohr", self.kpoints_per_bohr),
        ):
            if type(vectors) is not tuple or not vectors:
                raise ValueError(f"{label} must be a nonempty tuple")
            for vector in vectors:
                _validate_vector(vector, label)
        if len(self.kpoints_reduced) != len(self.kpoints_per_bohr):
            raise ValueError("k-point representations must have equal lengths")
        if (
            type(self.fft_grid) is not tuple
            or len(self.fft_grid) != 3
            or any(type(value) is not int or value <= 0 for value in self.fft_grid)
        ):
            raise ValueError("fft_grid must contain three positive integers")
        if type(self.band_count) is not int or self.band_count <= 0:
            raise ValueError("band_count must be positive")
        if type(self.spin_channel_count) is not int or self.spin_channel_count <= 0:
            raise ValueError("spin_channel_count must be positive")
        if type(
            self.spinor_component_count
        ) is not int or self.spinor_component_count not in {1, 2}:
            raise ValueError("spinor_component_count must be one or two")

    @staticmethod
    def signed_fft_frequency(index: int, size: int) -> int:
        """Return QE's signed frequency for one zero-based full-grid index."""
        if type(index) is not int or type(size) is not int:
            raise TypeError("index and size must be built-in integers")
        if size <= 0 or index < 0 or index >= size:
            raise IndexError("FFT index is outside its axis")
        if size % 2 == 0 and index == size // 2:
            raise ValueError(
                "even-grid Nyquist index has no unique signed G representative"
            )
        return index if index <= (size - 1) // 2 else index - size

    def _validate_grid_index(self, grid_index: tuple[int, int, int]) -> None:
        if (
            type(grid_index) is not tuple
            or len(grid_index) != 3
            or any(type(value) is not int for value in grid_index)
        ):
            raise TypeError("grid_index must contain three built-in integers")
        if any(
            index < 0 or index >= size
            for index, size in zip(grid_index, self.fft_grid, strict=True)
        ):
            raise IndexError("FFT index is outside its grid")

    def g_reduced(self, grid_index: tuple[int, int, int]) -> tuple[int, int, int]:
        """Map a full-grid index to source-ordered reciprocal coefficients."""
        self._validate_grid_index(grid_index)
        return (
            self.signed_fft_frequency(grid_index[0], self.fft_grid[0]),
            self.signed_fft_frequency(grid_index[1], self.fft_grid[1]),
            self.signed_fft_frequency(grid_index[2], self.fft_grid[2]),
        )

    def linear_grid_index(self, grid_index: tuple[int, int, int]) -> int:
        """Return zero-based native first-axis-fastest serialized index."""
        self._validate_grid_index(grid_index)
        ix, iy, iz = grid_index
        nx, ny, _ = self.fft_grid
        return ix + nx * (iy + ny * iz)

    def g_per_bohr(self, grid_index: tuple[int, int, int]) -> Vector3:
        """Return the physical Cartesian G vector for one full-grid index."""
        reduced = self.g_reduced(grid_index)
        return _row_vector_matrix_product(reduced, self.reciprocal_lattice_per_bohr)

    def kinetic_energy_hartree(
        self, kpoint_index: int, grid_index: tuple[int, int, int]
    ) -> float:
        """Evaluate ``0.5*|k+G|**2`` in Hartree, with zero-based indices."""
        if type(kpoint_index) is not int:
            raise TypeError("kpoint_index must be a built-in integer")
        if kpoint_index < 0 or kpoint_index >= len(self.kpoints_per_bohr):
            raise IndexError("kpoint_index is out of range")
        g_vector = self.g_per_bohr(grid_index)
        k_vector = self.kpoints_per_bohr[kpoint_index]
        return 0.5 * math.fsum(
            (k_component + g_component) ** 2
            for k_component, g_component in zip(k_vector, g_vector, strict=True)
        )


class _QexsdPlaneWaveDocument(Protocol):
    declared_unit_system_label: str
    atomic_structure_alat: float
    direct_lattice_vectors: Matrix3
    direct_lattice_source_label: str
    reciprocal_lattice_coefficients: Matrix3
    reciprocal_lattice_source_label: str
    species: tuple[tuple[str, float, str], ...]
    k_points: tuple[Vector3, ...]
    k_point_source_label: str
    sampled_k_point_count: int
    band_count: int
    fft_grid: tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class QePlaneWaveFrameExtractor:
    """Build one frame from the already parsed QEXSD document and UPF records."""

    duality_absolute_tolerance: float = 1.0e-10
    kpoint_reconstruction_tolerance: float = 1.0e-12

    def __post_init__(self) -> None:
        for label, value in (
            ("duality_absolute_tolerance", self.duality_absolute_tolerance),
            ("kpoint_reconstruction_tolerance", self.kpoint_reconstruction_tolerance),
        ):
            if type(value) is not float or not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{label} must be positive and finite")

    def extract(
        self,
        qexsd: QeQexsdData,
        *,
        pseudopotentials: tuple[QePseudopotentialFile, ...],
        overlap_metric: QeWavefunctionOverlapMetric,
        spin_channel_count: int,
        spinor_component_count: int,
    ) -> QePlaneWaveFrame:
        """Return a fail-closed frame without reparsing or rediscovering XML."""
        if type(qexsd) is not QeQexsdData:
            raise TypeError("qexsd must be QeQexsdData")
        if any(not hasattr(qexsd.document, name) for name in _REQUIRED_FIELDS):
            raise TypeError(
                "QEXSD document must be produced by QuantumEspressoXsdDocumentParser"
            )
        if type(pseudopotentials) is not tuple or not pseudopotentials:
            raise ValueError("pseudopotentials must be a nonempty tuple")
        if any(type(item) is not QePseudopotentialFile for item in pseudopotentials):
            raise TypeError(
                "pseudopotentials must contain QePseudopotentialFile values"
            )
        if type(overlap_metric) is not QeWavefunctionOverlapMetric:
            raise TypeError("overlap_metric must be a QeWavefunctionOverlapMetric")
        if type(spin_channel_count) is not int or spin_channel_count <= 0:
            raise ValueError("spin_channel_count must be positive")
        if type(spinor_component_count) is not int or spinor_component_count not in {
            1,
            2,
        }:
            raise ValueError("spinor_component_count must be one or two")
        document = cast("_QexsdPlaneWaveDocument", qexsd.document)
        if document.declared_unit_system_label != "Hartree atomic units":
            raise ValueError("unsupported QEXSD declared unit system")
        if document.sampled_k_point_count != len(document.k_points):
            raise ValueError("QEXSD k-point count is inconsistent")
        source_pseudos = tuple(item[2] for item in document.species)
        bound_pseudos = tuple(item.filename for item in pseudopotentials)
        if source_pseudos != bound_pseudos:
            raise ValueError("QEXSD pseudopotential labels disagree with bound UPFs")
        _validate_overlap_metric(pseudopotentials, overlap_metric)
        if (
            type(document.atomic_structure_alat) is not float
            or not math.isfinite(document.atomic_structure_alat)
            or document.atomic_structure_alat <= 0.0
        ):
            raise ValueError("QEXSD alat must be positive and finite")
        _validate_matrix(document.direct_lattice_vectors, "QEXSD direct lattice")
        _validate_matrix(
            document.reciprocal_lattice_coefficients,
            "QEXSD reciprocal lattice",
        )
        scale = 2.0 * math.pi / document.atomic_structure_alat
        reciprocal = tuple(
            tuple(component * scale for component in vector)
            for vector in document.reciprocal_lattice_coefficients
        )
        reciprocal_matrix = cast(Matrix3, reciprocal)
        direct_array = np.asarray(document.direct_lattice_vectors, dtype=np.float64)
        reciprocal_array = np.asarray(reciprocal_matrix, dtype=np.float64)
        duality = direct_array @ reciprocal_array.T
        if not np.allclose(
            duality,
            2.0 * math.pi * np.eye(3),
            rtol=0.0,
            atol=self.duality_absolute_tolerance,
        ):
            raise ValueError("QEXSD direct and reciprocal lattices are inconsistent")
        native_kpoints = np.asarray(document.k_points, dtype=np.float64)
        physical_kpoints = native_kpoints * scale
        try:
            reduced_array = np.linalg.solve(
                np.asarray(document.reciprocal_lattice_coefficients).T,
                native_kpoints.T,
            ).T
        except np.linalg.LinAlgError as error:
            raise ValueError("QEXSD reciprocal lattice is singular") from error
        reconstructed = reduced_array @ np.asarray(
            document.reciprocal_lattice_coefficients
        )
        if not np.allclose(
            reconstructed,
            native_kpoints,
            rtol=0.0,
            atol=self.kpoint_reconstruction_tolerance,
        ):
            raise ValueError(
                "QEXSD k-points cannot be represented in its reciprocal frame"
            )
        return QePlaneWaveFrame._from_extracted(
            qexsd=qexsd,
            pseudopotentials=pseudopotentials,
            reciprocal_scale_convention=(
                QeReciprocalScaleConvention.two_pi_over_alat_cartesian
            ),
            fft_g_vector_mapping=(
                QeFftGVectorMapping.first_axis_fastest_signed_fft_non_nyquist
            ),
            fourier_convention=(
                QeUnkFourierConvention.forward_negative_exponent_divide_by_grid_size
            ),
            overlap_metric=overlap_metric,
            direct_lattice_bohr=document.direct_lattice_vectors,
            reciprocal_lattice_per_bohr=reciprocal_matrix,
            kpoints_reduced=_array_vectors(reduced_array),
            kpoints_per_bohr=_array_vectors(physical_kpoints),
            fft_grid=document.fft_grid,
            band_count=document.band_count,
            spin_channel_count=spin_channel_count,
            spinor_component_count=spinor_component_count,
        )


def _validate_overlap_metric(
    pseudopotentials: tuple[QePseudopotentialFile, ...],
    overlap_metric: QeWavefunctionOverlapMetric,
) -> None:
    formalisms = tuple(
        _classify_pseudopotential_formalism(item.pseudopotential.formalism)
        for item in pseudopotentials
    )
    observed = set(formalisms)
    has_ultrasoft = _QePseudopotentialFormalism.ultrasoft in observed
    has_paw = _QePseudopotentialFormalism.paw in observed
    if overlap_metric is QeWavefunctionOverlapMetric.identity and observed != {
        _QePseudopotentialFormalism.norm_conserving
    }:
        raise ValueError("identity overlap requires only bound norm-conserving UPFs")
    if overlap_metric is QeWavefunctionOverlapMetric.ultrasoft_generalized and (
        not has_ultrasoft or has_paw
    ):
        raise ValueError("ultrasoft overlap requires ultrasoft and no PAW UPFs")
    if overlap_metric is QeWavefunctionOverlapMetric.paw_generalized and (
        not has_paw or has_ultrasoft
    ):
        raise ValueError("PAW overlap requires PAW and no ultrasoft UPFs")


def _classify_pseudopotential_formalism(
    value: str,
) -> _QePseudopotentialFormalism:
    normalized = " ".join(value.casefold().replace("-", " ").replace("_", " ").split())
    aliases = {
        "norm conserving": _QePseudopotentialFormalism.norm_conserving,
        "nc": _QePseudopotentialFormalism.norm_conserving,
        "ncpp": _QePseudopotentialFormalism.norm_conserving,
        "ultrasoft": _QePseudopotentialFormalism.ultrasoft,
        "ultra soft": _QePseudopotentialFormalism.ultrasoft,
        "uspp": _QePseudopotentialFormalism.ultrasoft,
        "paw": _QePseudopotentialFormalism.paw,
        "projector augmented wave": _QePseudopotentialFormalism.paw,
    }
    try:
        return aliases[normalized]
    except KeyError as error:
        raise ValueError(
            f"unsupported QE pseudopotential formalism: {value!r}"
        ) from error


def _array_vectors(
    array: np.ndarray[tuple[int, ...], np.dtype[np.float64]],
) -> tuple[Vector3, ...]:
    if array.ndim != 2 or array.shape[1] != 3:
        raise ValueError("array must have shape (count, 3)")
    return tuple((float(row[0]), float(row[1]), float(row[2])) for row in array)


def _validate_matrix(value: Matrix3, label: str) -> None:
    if type(value) is not tuple or len(value) != 3:
        raise ValueError(f"{label} must contain three vectors")
    for vector in value:
        _validate_vector(vector, label)


def _validate_vector(value: Vector3, label: str) -> None:
    if type(value) is not tuple or len(value) != 3:
        raise ValueError(f"{label} vectors must contain three components")
    if any(
        type(component) is not float or not math.isfinite(component)
        for component in value
    ):
        raise ValueError(f"{label} components must be finite built-in floats")


def _row_vector_matrix_product(
    vector: tuple[int, int, int], matrix: Matrix3
) -> Vector3:
    return cast(
        Vector3,
        tuple(
            math.fsum(vector[row] * matrix[row][column] for row in range(3))
            for column in range(3)
        ),
    )


__all__ = [
    "QeFftGVectorMapping",
    "QePlaneWaveFrame",
    "QePlaneWaveFrameExtractor",
    "QeReciprocalScaleConvention",
    "QeUnkFourierConvention",
    "QeWavefunctionOverlapMetric",
]
