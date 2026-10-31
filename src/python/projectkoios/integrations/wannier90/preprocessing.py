"""Represent and render exact Wannier90 preprocessing input."""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass

import numpy as np

from projectkoios.integrations.wannier90._parsing import Wannier90ParserLimits
from projectkoios.integrations.wannier90.nnkp import (
    Wannier90NnkpData,
    Wannier90NnkpParser,
)
from projectkoios.physkit.numerics.typing.numpy.arrays import RealVector
from projectkoios.physkit.periodic import DirectLattice3D, ReciprocalLattice3D
from projectkoios.physkit.periodic.unit_cell import UnitCell
from projectkoios.physkit.units import (
    MatrixQuantity,
    ModelSystemUnitConverter,
    PhysicalUnit,
    ScalarQuantity,
    Unitless,
)
from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.calculator_input import (
    CalculatorInputArtifact,
    CalculatorInputMapping,
    CalculatorInputRecord,
    CalculatorInputSourceReference,
)

_SEEDNAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")
_ELEMENT_SYMBOL = re.compile(r"[A-Z][a-z]?\Z")
_ANGSTROM = PhysicalUnit("angstrom")
_INVERSE_ANGSTROM = PhysicalUnit("1 / angstrom")
_ANGSTROM_SQUARED = PhysicalUnit("angstrom ** 2")
_ELECTRON_VOLT = PhysicalUnit("eV")

type Wannier90Vector3 = tuple[float, float, float]
type Wannier90LatticeVectors = tuple[
    Wannier90Vector3,
    Wannier90Vector3,
    Wannier90Vector3,
]
type Wannier90FractionalAtom = tuple[str, Wannier90Vector3]

WANNIER90_INTEGRATION_ID = CalculatorIntegrationId(value="wannier90")


@dataclass(frozen=True, slots=True)
class Wannier90PreprocessingInput:
    """Represent and render generic non-spin spectral native ``.win`` input."""

    input_id: str
    source: CalculatorInputSourceReference
    seedname: str
    calculator_version_constraint: str
    num_bands: int
    num_wann: int
    unit_cell: UnitCell
    projections: tuple[str, ...]
    mp_grid: tuple[int, int, int]
    kpoints_reciprocal_fractional: MatrixQuantity
    localization_iterations: int
    localization_tolerance: ScalarQuantity
    localization_convergence_window: int
    write_hr: bool
    excluded_bands: tuple[int, ...] = ()
    selected_projection_indices: tuple[int, ...] = ()
    outer_window: tuple[ScalarQuantity, ScalarQuantity] | None = None
    frozen_window: tuple[ScalarQuantity, ScalarQuantity] | None = None
    disentanglement_iterations: int | None = None
    disentanglement_tolerance: ScalarQuantity | None = None
    disentanglement_convergence_window: int | None = None
    disentanglement_mix_ratio: ScalarQuantity | None = None
    coordinate_precision: int = 10

    def __post_init__(self) -> None:
        _validate_source_and_seedname(self.source, self.seedname)
        for name, value in (
            ("input_id", self.input_id),
            ("calculator_version_constraint", self.calculator_version_constraint),
        ):
            if type(value) is not str or not value or value != value.strip():
                raise ValueError(f"{name} must be nonempty and stripped")
        _positive_integer(self.num_bands, "num_bands")
        _positive_integer(self.num_wann, "num_wann")
        if self.num_wann > self.num_bands:
            raise ValueError("num_wann must not exceed num_bands")
        _positive_integer(
            self.localization_iterations,
            "localization_iterations",
        )
        _positive_quantity_magnitude(
            self.localization_tolerance,
            _ANGSTROM_SQUARED,
            "localization_tolerance",
        )
        _positive_integer(
            self.localization_convergence_window,
            "localization_convergence_window",
        )
        if type(self.write_hr) is not bool:
            raise TypeError("write_hr must be a bool")
        if (
            type(self.coordinate_precision) is not int
            or not 1 <= self.coordinate_precision <= 17
        ):
            raise ValueError("coordinate_precision must be an integer from 1 to 17")
        if not isinstance(self.unit_cell, UnitCell):
            raise TypeError("unit_cell must be a PhysKit UnitCell")
        rounded_lattice = tuple(
            _rounded_vector(vector, self.coordinate_precision)
            for vector in self.lattice_vectors_angstrom
        )
        _direct_lattice(rounded_lattice)
        _validate_atoms(self.atoms_fractional)
        _validate_projections(self.projections)
        _validate_positive_indices(self.excluded_bands, "excluded_bands")
        _validate_positive_indices(
            self.selected_projection_indices,
            "selected_projection_indices",
        )
        if (
            self.selected_projection_indices
            and len(self.selected_projection_indices) != self.num_wann
        ):
            raise ValueError(
                "selected_projection_indices must contain exactly num_wann indices"
            )
        _validate_mesh_and_kpoints(
            self.mp_grid,
            self.kpoints_reciprocal_fractional,
        )
        _validate_disentanglement(
            num_bands=self.num_bands,
            num_wann=self.num_wann,
            outer_window=self.outer_window,
            frozen_window=self.frozen_window,
            iterations=self.disentanglement_iterations,
            tolerance=self.disentanglement_tolerance,
            convergence_window=self.disentanglement_convergence_window,
            mix_ratio=self.disentanglement_mix_ratio,
        )

    @property
    def lattice_vectors_angstrom(self) -> Wannier90LatticeVectors:
        """Return source-ordered physical lattice vectors as angstrom rows."""
        factor = ModelSystemUnitConverter.conversion_factor(
            self.unit_cell.H.unit,
            _ANGSTROM,
        )
        matrix = self.unit_cell.H.magnitude * factor
        return (
            _array_vector3(matrix[:, 0]),
            _array_vector3(matrix[:, 1]),
            _array_vector3(matrix[:, 2]),
        )

    @property
    def atoms_fractional(self) -> tuple[Wannier90FractionalAtom, ...]:
        """Return source-ordered symbols and unitless fractional positions."""
        return tuple(
            (
                atom.symbol,
                _array_vector3(atom.position_fractional.magnitude),
            )
            for atom in self.unit_cell.atomic_basis.atoms
        )

    @property
    def kpoint_vectors_reciprocal_fractional(
        self,
    ) -> tuple[Wannier90Vector3, ...]:
        """Return source-ordered unitless reciprocal-fractional k points."""
        return tuple(
            _array_vector3(row) for row in self.kpoints_reciprocal_fractional.magnitude
        )

    @property
    def input_filename(self) -> str:
        """Return the seed-derived native input basename."""
        return f"{self.seedname}.win"

    @property
    def nnkp_filename(self) -> str:
        """Return the seed-derived preprocessing output basename."""
        return f"{self.seedname}.nnkp"

    def render(self) -> bytes:
        """Render deterministic newline-terminated ASCII ``.win`` bytes."""
        localization_tolerance_angstrom2 = _quantity_magnitude(
            self.localization_tolerance,
            _ANGSTROM_SQUARED,
            "localization_tolerance",
        )
        outer_window_ev = _window_magnitudes(self.outer_window, _ELECTRON_VOLT)
        frozen_window_ev = _window_magnitudes(self.frozen_window, _ELECTRON_VOLT)
        disentanglement_tolerance_angstrom2 = (
            _quantity_magnitude(
                self.disentanglement_tolerance,
                _ANGSTROM_SQUARED,
                "disentanglement_tolerance",
            )
            if self.disentanglement_tolerance is not None
            else None
        )
        disentanglement_mix_ratio = (
            _unitless_magnitude(
                self.disentanglement_mix_ratio,
                "disentanglement_mix_ratio",
            )
            if self.disentanglement_mix_ratio is not None
            else None
        )
        lines = [
            f"num_bands = {self.num_bands}",
            f"num_wann = {self.num_wann}",
            "spinors = .false.",
            f"num_iter = {self.localization_iterations}",
            "conv_tol = "
            + _format_scalar(
                localization_tolerance_angstrom2,
                self.coordinate_precision,
            ),
            f"conv_window = {self.localization_convergence_window}",
        ]
        if self.excluded_bands:
            lines.append("exclude_bands = " + ", ".join(map(str, self.excluded_bands)))
        if self.selected_projection_indices:
            lines.append(
                "select_projections = "
                + ", ".join(map(str, self.selected_projection_indices))
            )
        if outer_window_ev is not None:
            lines.extend(
                (
                    "dis_win_min = "
                    + _format_scalar(
                        outer_window_ev[0],
                        self.coordinate_precision,
                    ),
                    "dis_win_max = "
                    + _format_scalar(
                        outer_window_ev[1],
                        self.coordinate_precision,
                    ),
                )
            )
        if frozen_window_ev is not None:
            lines.extend(
                (
                    "dis_froz_min = "
                    + _format_scalar(
                        frozen_window_ev[0],
                        self.coordinate_precision,
                    ),
                    "dis_froz_max = "
                    + _format_scalar(
                        frozen_window_ev[1],
                        self.coordinate_precision,
                    ),
                )
            )
        if self.disentanglement_iterations is not None:
            assert disentanglement_tolerance_angstrom2 is not None
            assert self.disentanglement_convergence_window is not None
            assert disentanglement_mix_ratio is not None
            lines.extend(
                (
                    f"dis_num_iter = {self.disentanglement_iterations}",
                    "dis_conv_tol = "
                    + _format_scalar(
                        disentanglement_tolerance_angstrom2,
                        self.coordinate_precision,
                    ),
                    f"dis_conv_window = {self.disentanglement_convergence_window}",
                    "dis_mix_ratio = "
                    + _format_scalar(
                        disentanglement_mix_ratio,
                        self.coordinate_precision,
                    ),
                )
            )
        lines.extend((f"write_hr = {_logical(self.write_hr)}", "length_unit = ang", ""))
        lines.extend(("begin unit_cell_cart", "ang"))
        lines.extend(
            _format_vector(vector, self.coordinate_precision)
            for vector in self.lattice_vectors_angstrom
        )
        lines.extend(("end unit_cell_cart", "", "begin atoms_frac"))
        lines.extend(
            f"{symbol} {_format_vector(position, self.coordinate_precision)}"
            for symbol, position in self.atoms_fractional
        )
        lines.extend(("end atoms_frac", "", "begin projections"))
        lines.extend(self.projections)
        lines.extend(
            (
                "end projections",
                "",
                f"mp_grid = {self.mp_grid[0]} {self.mp_grid[1]} {self.mp_grid[2]}",
                "",
                "begin kpoints",
            )
        )
        lines.extend(
            _format_vector(kpoint, self.coordinate_precision)
            for kpoint in self.kpoint_vectors_reciprocal_fractional
        )
        lines.append("end kpoints")
        return ("\n".join(lines) + "\n").encode("ascii")

    def prepare(self) -> CalculatorInputRecord:
        """Return an authenticated prepared record for the rendered input."""
        content = self.render()
        return _prepared_record(
            input_id=self.input_id,
            source=self.source,
            seedname=self.seedname,
            content=content,
            expected_sha256=hashlib.sha256(content).hexdigest(),
            calculator_version_constraint=self.calculator_version_constraint,
            operation=(
                "projectkoios.integrations.wannier90.Wannier90PreprocessingInput.prepare"
            ),
        )


@dataclass(frozen=True, slots=True)
class Wannier90PreprocessingNnkpOutput:
    """Retain and parse one observed seed-bound preprocessing topology output."""

    preprocessing_input: Wannier90PreprocessingInput
    content: bytes
    parser_limits: Wannier90ParserLimits = Wannier90ParserLimits()

    def __post_init__(self) -> None:
        if type(self.preprocessing_input) is not Wannier90PreprocessingInput:
            raise TypeError("preprocessing_input must be Wannier90PreprocessingInput")
        if type(self.content) is not bytes or not self.content:
            raise ValueError("content must be nonempty exact bytes")
        if type(self.parser_limits) is not Wannier90ParserLimits:
            raise TypeError("parser_limits must be Wannier90ParserLimits")

    @property
    def seedname(self) -> str:
        """Return the seed declared by the preprocessing input."""
        return self.preprocessing_input.seedname

    @property
    def filename(self) -> str:
        """Return the seed-derived NNKP basename."""
        return self.preprocessing_input.nnkp_filename

    @property
    def byte_size(self) -> int:
        """Return the observed output byte size."""
        return len(self.content)

    @property
    def sha256(self) -> str:
        """Return the observed output SHA-256 digest."""
        return hashlib.sha256(self.content).hexdigest()

    def parse(self) -> Wannier90NnkpData:
        """Parse observed bytes with the declared bounded parser limits."""
        return Wannier90NnkpParser(self.parser_limits).execute(self.content)

    def verify_source_selected_projection_indices(self) -> Wannier90NnkpData:
        """Verify selected source indices against the expanded native inventory."""
        parsed = self.parse()
        selected = self.preprocessing_input.selected_projection_indices
        if selected and max(selected) > len(parsed.projections):
            raise ValueError(
                "selected projection index exceeds the native projection inventory"
            )
        return parsed

    def verify_source_lattices_kpoints_and_excluded_bands(
        self,
        *,
        direct_lattice_absolute_tolerance: ScalarQuantity,
        reciprocal_lattice_absolute_tolerance: ScalarQuantity,
        kpoint_fractional_absolute_tolerance: ScalarQuantity,
    ) -> Wannier90NnkpData:
        """Verify the named source semantics under explicit comparison tolerances."""
        parsed = self.parse()
        direct_tolerance_angstrom = _nonnegative_quantity_magnitude(
            direct_lattice_absolute_tolerance,
            _ANGSTROM,
            "direct_lattice_absolute_tolerance",
        )
        reciprocal_tolerance_per_angstrom = _nonnegative_quantity_magnitude(
            reciprocal_lattice_absolute_tolerance,
            _INVERSE_ANGSTROM,
            "reciprocal_lattice_absolute_tolerance",
        )
        kpoint_fractional_tolerance = _nonnegative_unitless_magnitude(
            kpoint_fractional_absolute_tolerance,
            "kpoint_fractional_absolute_tolerance",
        )
        expected_lattice = tuple(
            _rounded_vector(vector, self.preprocessing_input.coordinate_precision)
            for vector in self.preprocessing_input.lattice_vectors_angstrom
        )
        expected_reciprocal_lattice = _reciprocal_lattice(expected_lattice)
        expected_kpoints = tuple(
            _rounded_vector(vector, self.preprocessing_input.coordinate_precision)
            for vector in self.preprocessing_input.kpoint_vectors_reciprocal_fractional
        )
        if not _coordinate_inventories_close(
            parsed.real_lattice,
            expected_lattice,
            direct_tolerance_angstrom,
        ):
            raise ValueError("NNKP real lattice disagrees with preprocessing input")
        if not _coordinate_inventories_close(
            parsed.reciprocal_lattice,
            expected_reciprocal_lattice,
            reciprocal_tolerance_per_angstrom,
        ):
            raise ValueError(
                "NNKP reciprocal lattice disagrees with preprocessing input"
            )
        if not _coordinate_inventories_close(
            parsed.kpoints,
            expected_kpoints,
            kpoint_fractional_tolerance,
        ):
            raise ValueError(
                "NNKP k-points disagree with preprocessing input order or values"
            )
        if parsed.excluded_bands != self.preprocessing_input.excluded_bands:
            raise ValueError("NNKP excluded bands disagree with preprocessing input")
        return parsed


def _rounded_coordinate(value: float, precision: int) -> float:
    return float(f"{0.0 if value == 0.0 else value:.{precision}f}")


def _rounded_vector(vector: Wannier90Vector3, precision: int) -> Wannier90Vector3:
    return (
        _rounded_coordinate(vector[0], precision),
        _rounded_coordinate(vector[1], precision),
        _rounded_coordinate(vector[2], precision),
    )


def _direct_lattice(
    vectors: tuple[Wannier90Vector3, ...],
) -> DirectLattice3D:
    first, second, third = vectors
    return DirectLattice3D(
        a1=np.asarray(first, dtype=np.float64),
        a2=np.asarray(second, dtype=np.float64),
        a3=np.asarray(third, dtype=np.float64),
    )


def _reciprocal_lattice(
    direct_lattice: tuple[Wannier90Vector3, ...],
) -> tuple[Wannier90Vector3, ...]:
    reciprocal_lattice = ReciprocalLattice3D.from_direct_lattice(
        _direct_lattice(direct_lattice)
    )
    return (
        _array_vector3(reciprocal_lattice.b1),
        _array_vector3(reciprocal_lattice.b2),
        _array_vector3(reciprocal_lattice.b3),
    )


def _coordinate_inventories_close(
    observed: tuple[Wannier90Vector3, ...],
    expected: tuple[Wannier90Vector3, ...],
    absolute_tolerance: float,
) -> bool:
    return len(observed) == len(expected) and all(
        abs(observed_value - expected_value) <= absolute_tolerance
        for observed_vector, expected_vector in zip(observed, expected, strict=True)
        for observed_value, expected_value in zip(
            observed_vector,
            expected_vector,
            strict=True,
        )
    )


def _validate_source_and_seedname(
    source: CalculatorInputSourceReference,
    seedname: str,
) -> None:
    if type(source) is not CalculatorInputSourceReference:
        raise TypeError("source must be a CalculatorInputSourceReference")
    if type(seedname) is not str or _SEEDNAME.fullmatch(seedname) is None:
        raise ValueError("seedname must be a safe nonempty Wannier90 basename")


def _positive_integer(value: int, name: str) -> None:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _array_vector3(values: RealVector) -> Wannier90Vector3:
    if values.shape != (3,):
        raise ValueError("numeric vector must contain three values")
    return float(values[0]), float(values[1]), float(values[2])


def _quantity_magnitude(
    quantity: ScalarQuantity,
    target: PhysicalUnit,
    name: str,
) -> float:
    if type(quantity) is not ScalarQuantity:
        raise TypeError(f"{name} must be a PhysKit ScalarQuantity")
    try:
        converted = ModelSystemUnitConverter.convert_scalar(quantity, target)
    except ValueError as error:
        raise ValueError(f"{name} has incompatible physical units") from error
    return converted.magnitude


def _unitless_magnitude(quantity: ScalarQuantity, name: str) -> float:
    if type(quantity) is not ScalarQuantity:
        raise TypeError(f"{name} must be a PhysKit ScalarQuantity")
    if not isinstance(quantity.unit, Unitless):
        raise ValueError(f"{name} must be explicitly unitless")
    return quantity.magnitude


def _positive_quantity_magnitude(
    quantity: ScalarQuantity,
    target: PhysicalUnit,
    name: str,
) -> float:
    value = _quantity_magnitude(quantity, target, name)
    if value <= 0.0:
        raise ValueError(f"{name} must be positive")
    return value


def _nonnegative_quantity_magnitude(
    quantity: ScalarQuantity,
    target: PhysicalUnit,
    name: str,
) -> float:
    value = _quantity_magnitude(quantity, target, name)
    if value < 0.0:
        raise ValueError(f"{name} must be nonnegative")
    return value


def _nonnegative_unitless_magnitude(quantity: ScalarQuantity, name: str) -> float:
    value = _unitless_magnitude(quantity, name)
    if value < 0.0:
        raise ValueError(f"{name} must be nonnegative")
    return value


def _validate_vector(vector: Wannier90Vector3, name: str) -> None:
    if type(vector) is not tuple or len(vector) != 3:
        raise ValueError(f"{name} must be a three-value tuple")
    if any(type(value) is not float or not math.isfinite(value) for value in vector):
        raise ValueError(f"{name} values must be finite floats")


def _validate_atoms(atoms: tuple[Wannier90FractionalAtom, ...]) -> None:
    if type(atoms) is not tuple or not atoms:
        raise ValueError("atoms_fractional must be a nonempty tuple")
    for index, atom in enumerate(atoms):
        if type(atom) is not tuple or len(atom) != 2:
            raise ValueError("each fractional atom must be a symbol-position tuple")
        symbol, position = atom
        if type(symbol) is not str or _ELEMENT_SYMBOL.fullmatch(symbol) is None:
            raise ValueError("fractional atom symbols must be element symbols")
        _validate_vector(position, f"fractional atom {index}")


def _validate_projections(projections: tuple[str, ...]) -> None:
    if type(projections) is not tuple or not projections:
        raise ValueError("projections must be a nonempty tuple")
    for projection in projections:
        if (
            type(projection) is not str
            or not projection
            or projection != projection.strip()
            or any(character in projection for character in ("\0", "\n", "\r", "!"))
        ):
            raise ValueError("projection lines must be safe nonempty native values")
        try:
            projection.encode("ascii")
        except UnicodeEncodeError as error:
            raise ValueError("projection lines must be ASCII") from error


def _validate_positive_indices(values: tuple[int, ...], name: str) -> None:
    if type(values) is not tuple:
        raise TypeError(f"{name} must be a tuple")
    if any(type(value) is not int or value <= 0 for value in values):
        raise ValueError(f"{name} must contain positive integers")
    if len(values) != len(set(values)):
        raise ValueError(f"{name} must not contain duplicates")


def _validate_mesh_and_kpoints(
    mp_grid: tuple[int, int, int],
    kpoints: MatrixQuantity,
) -> None:
    if type(mp_grid) is not tuple or len(mp_grid) != 3:
        raise ValueError("mp_grid must be a three-value tuple")
    if any(type(value) is not int or value <= 0 for value in mp_grid):
        raise ValueError("mp_grid values must be positive integers")
    if type(kpoints) is not MatrixQuantity:
        raise TypeError("kpoints_reciprocal_fractional must be MatrixQuantity")
    if not isinstance(kpoints.unit, Unitless):
        raise ValueError("kpoints_reciprocal_fractional must be unitless")
    if kpoints.magnitude.ndim != 2 or kpoints.magnitude.shape[1] != 3:
        raise ValueError("kpoints_reciprocal_fractional must have shape (count, 3)")
    if kpoints.magnitude.shape[0] != math.prod(mp_grid):
        raise ValueError("k-point count must equal the mp_grid product")
    vectors = tuple(_array_vector3(row) for row in kpoints.magnitude)
    if len(vectors) != len(set(vectors)):
        raise ValueError("k-points must not contain duplicates")


def _window_magnitudes(
    window: tuple[ScalarQuantity, ScalarQuantity] | None,
    target: PhysicalUnit,
) -> tuple[float, float] | None:
    if window is None:
        return None
    if type(window) is not tuple or len(window) != 2:
        raise ValueError("energy window must be a lower-upper tuple")
    lower = _quantity_magnitude(window[0], target, "energy window lower bound")
    upper = _quantity_magnitude(window[1], target, "energy window upper bound")
    if lower >= upper:
        raise ValueError("energy window lower bound must be less than upper bound")
    return lower, upper


def _validate_disentanglement(
    *,
    num_bands: int,
    num_wann: int,
    outer_window: tuple[ScalarQuantity, ScalarQuantity] | None,
    frozen_window: tuple[ScalarQuantity, ScalarQuantity] | None,
    iterations: int | None,
    tolerance: ScalarQuantity | None,
    convergence_window: int | None,
    mix_ratio: ScalarQuantity | None,
) -> None:
    values = (iterations, tolerance, convergence_window, mix_ratio)
    if num_wann == num_bands:
        if outer_window is not None or frozen_window is not None:
            raise ValueError("energy windows require a disentangled construction")
        if any(value is not None for value in values):
            raise ValueError("disentanglement controls require num_wann < num_bands")
        return
    if outer_window is None:
        raise ValueError("an outer energy window is required for disentanglement")
    if any(value is None for value in values):
        raise ValueError("all disentanglement controls must be supplied")
    outer_ev = _window_magnitudes(outer_window, _ELECTRON_VOLT)
    frozen_ev = _window_magnitudes(frozen_window, _ELECTRON_VOLT)
    assert outer_ev is not None
    if frozen_ev is not None and (
        frozen_ev[0] < outer_ev[0] or frozen_ev[1] > outer_ev[1]
    ):
        raise ValueError("frozen_window must lie inside outer_window")
    assert iterations is not None
    assert tolerance is not None
    assert convergence_window is not None
    assert mix_ratio is not None
    _positive_integer(iterations, "disentanglement_iterations")
    _positive_quantity_magnitude(
        tolerance,
        _ANGSTROM_SQUARED,
        "disentanglement_tolerance",
    )
    _positive_integer(convergence_window, "disentanglement_convergence_window")
    mix_value = _unitless_magnitude(mix_ratio, "disentanglement_mix_ratio")
    if not 0.0 < mix_value <= 1.0:
        raise ValueError("disentanglement_mix_ratio must lie in (0, 1]")


def _format_scalar(value: float, precision: int) -> str:
    return f"{0.0 if value == 0.0 else value:.{precision}g}"


def _format_vector(vector: Wannier90Vector3, precision: int) -> str:
    return " ".join(
        f"{0.0 if value == 0.0 else value:.{precision}f}" for value in vector
    )


def _logical(value: bool) -> str:
    return ".true." if value else ".false."


def _prepared_record(
    *,
    input_id: str,
    source: CalculatorInputSourceReference,
    seedname: str,
    content: bytes,
    expected_sha256: str,
    calculator_version_constraint: str,
    operation: str,
) -> CalculatorInputRecord:
    filename = f"{seedname}.win"
    return CalculatorInputRecord(
        input_id=input_id,
        schema_version=1,
        source=source,
        integration_id=WANNIER90_INTEGRATION_ID,
        calculator_name="wannier90.x",
        calculator_version_constraint=calculator_version_constraint,
        representation="wannier90-win",
        artifacts=(
            CalculatorInputArtifact(
                role="wannier90-input",
                filename=filename,
                media_type="text/plain; charset=us-ascii",
                content=content,
                byte_size=len(content),
                sha256=expected_sha256,
            ),
        ),
        external_requirements=(),
        mappings=(
            CalculatorInputMapping(
                neutral_field="wannier90.seedname",
                neutral_value=seedname,
                native_fields=("input filename",),
                native_values=(filename,),
                effect="identity",
                qualification=(
                    "Caller-declared seed name fixes the native preprocessing "
                    "input filename."
                ),
            ),
        ),
        preparation_operation=operation,
        preparation_version="1",
    )
