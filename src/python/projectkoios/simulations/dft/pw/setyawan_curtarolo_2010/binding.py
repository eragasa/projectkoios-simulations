"""Bind Appendix-A paths to exact simulation cells.

For row-vector direct bases, binding validates ``A = U S R`` with integer-
unimodular ``U`` and proper Cartesian rotation ``R``.  Since the simulation
reciprocal basis is ``U**(-T) B_S R``, reciprocal-fractional path rows obey
``q_A = q_S U**T``.  Rotation-invariant lengths validate the Gram matrix in
angstrom without turning the public tolerance into a squared quantity.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from projectkoios.physkit.core.actions import DataObjectActionizer
from projectkoios.physkit.core.data import DataObject
from projectkoios.physkit.core.results import ResultsObject
from projectkoios.simulations.dft.pw.bands import (
    BandPath,
    BandPathBranch,
    BandPathConventionProvenance,
    BandPathCoordinateSystem,
    BandPathDirectBasisTransform,
    BandPathVertex,
    PwDftBandsSimulation,
)
from projectkoios.simulations.dft.pw.setyawan_curtarolo_2010._linear_algebra import (
    _determinant,
    _identity_matrix,
    _inverse,
    _matrix_product,
    _norm,
    _row_vector_matrix_product,
    _subtract,
    _transpose,
)
from projectkoios.simulations.dft.pw.setyawan_curtarolo_2010.appendix_a import (
    _path_data,
)
from projectkoios.simulations.dft.pw.setyawan_curtarolo_2010.lattice import (
    SetyawanCurtaroloLattice,
)
from projectkoios.simulations.dft.pw.setyawan_curtarolo_2010.model import (
    SETYAWAN_CURTAROLO_CONVENTION_NAME,
    SETYAWAN_CURTAROLO_DOI,
    SETYAWAN_CURTAROLO_REVISION,
)
from projectkoios.simulations.dft.pw.simulation import PwDftSimulation, PwMatrix3

_IDENTITY_DIRECT_BASIS_TRANSFORM: BandPathDirectBasisTransform = (
    (1, 0, 0),
    (0, 1, 0),
    (0, 0, 1),
)


@dataclass(frozen=True, slots=True)
class SetyawanCurtaroloPathDefinition(DataObject):
    """Retain one Appendix-A path definition for a declared lattice case."""

    lattice: SetyawanCurtaroloLattice

    def __post_init__(self) -> None:
        if type(self.lattice) is not SetyawanCurtaroloLattice:
            raise TypeError("lattice must be a SetyawanCurtaroloLattice")

    @property
    def standard_special_points(self) -> tuple[BandPathVertex, ...]:
        """Return all tabulated points in the paper's reciprocal basis."""
        points, _ = _path_data(self.lattice)
        return tuple(
            BandPathVertex(label=label, coordinates=coordinates)
            for label, coordinates in points.items()
        )

    @property
    def path(self) -> BandPath:
        """Return the paper-defined path in its standard reciprocal basis."""
        return self._path_with_transform(
            _identity_matrix(),
            direct_basis_transform=_IDENTITY_DIRECT_BASIS_TRANSFORM,
        )

    def _path_with_transform(
        self,
        transform: PwMatrix3,
        *,
        direct_basis_transform: BandPathDirectBasisTransform,
    ) -> BandPath:
        points, branches = _path_data(self.lattice)
        transformed = {
            label: _row_vector_matrix_product(coordinates, transform)
            for label, coordinates in points.items()
        }
        provenance = BandPathConventionProvenance(
            convention_name=SETYAWAN_CURTAROLO_CONVENTION_NAME,
            convention_revision=SETYAWAN_CURTAROLO_REVISION,
            source_doi=SETYAWAN_CURTAROLO_DOI,
            bravais_lattice=self.lattice.bravais_lattice.value,
            appendix_a_case=self.lattice.appendix_a_case.value,
            direct_basis_transform=direct_basis_transform,
        )
        basis_note = "; basis-transformed" if provenance.basis_transformed else ""
        return BandPath(
            branches=tuple(
                BandPathBranch(
                    vertices=tuple(
                        BandPathVertex(label=label, coordinates=transformed[label])
                        for label in branch
                    )
                )
                for branch in branches
            ),
            coordinate_system=BandPathCoordinateSystem.reciprocal_fractional,
            convention=(
                f"{SETYAWAN_CURTAROLO_CONVENTION_NAME} 2010 "
                f"{self.lattice.appendix_a_case.value}{basis_note}; "
                f"doi:{SETYAWAN_CURTAROLO_DOI}"
            ),
            provenance=provenance,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class SetyawanCurtaroloPathBindingRequest(DataObject):
    """Request binding of one convention path to one exact simulation cell."""

    definition: SetyawanCurtaroloPathDefinition
    simulation: PwDftSimulation
    direct_basis_transform: BandPathDirectBasisTransform | None = None
    lattice_tolerance_angstrom: float = 1.0e-8

    def __post_init__(self) -> None:
        if type(self.definition) is not SetyawanCurtaroloPathDefinition:
            raise TypeError("definition must be a SetyawanCurtaroloPathDefinition")
        if type(self.simulation) is not PwDftSimulation:
            raise TypeError("simulation must be a PwDftSimulation")
        if self.direct_basis_transform is not None:
            _validated_integer_basis_transform(self.direct_basis_transform)
        if type(self.lattice_tolerance_angstrom) is not float:
            raise TypeError("lattice_tolerance_angstrom must be a built-in float")
        if (
            not math.isfinite(self.lattice_tolerance_angstrom)
            or self.lattice_tolerance_angstrom <= 0.0
        ):
            raise ValueError("lattice_tolerance_angstrom must be positive and finite")


class SetyawanCurtaroloBasisTransformSource(StrEnum):
    """Identify whether the binding transform was declared or recovered."""

    declared = "declared"
    recovered = "recovered"


@dataclass(frozen=True, slots=True, kw_only=True)
class SetyawanCurtaroloPathBindingResult(ResultsObject):
    """Correlate one binding request with its cell-bound calculation."""

    request: SetyawanCurtaroloPathBindingRequest
    calculation: PwDftBandsSimulation
    basis_transform_source: SetyawanCurtaroloBasisTransformSource

    def __post_init__(self) -> None:
        if type(self.request) is not SetyawanCurtaroloPathBindingRequest:
            raise TypeError("request must be a SetyawanCurtaroloPathBindingRequest")
        if type(self.calculation) is not PwDftBandsSimulation:
            raise TypeError("calculation must be a PwDftBandsSimulation")
        if type(self.basis_transform_source) is not (
            SetyawanCurtaroloBasisTransformSource
        ):
            raise TypeError(
                "basis_transform_source must be a SetyawanCurtaroloBasisTransformSource"
            )
        if self.calculation.simulation is not self.request.simulation:
            raise ValueError("bound calculation must retain the requested simulation")
        provenance = self.calculation.path.provenance
        if provenance is None:
            raise ValueError("bound calculation path must retain provenance")
        if (
            provenance.bravais_lattice
            != self.request.definition.lattice.bravais_lattice.value
            or provenance.appendix_a_case
            != self.request.definition.lattice.appendix_a_case.value
        ):
            raise ValueError(
                "bound path provenance must match the requested definition"
            )
        declared = self.request.direct_basis_transform
        if declared is None:
            if (
                self.basis_transform_source
                is not SetyawanCurtaroloBasisTransformSource.recovered
            ):
                raise ValueError(
                    "omitted basis transform must be recorded as recovered"
                )
        elif (
            self.basis_transform_source
            is not SetyawanCurtaroloBasisTransformSource.declared
            or provenance.direct_basis_transform != declared
        ):
            raise ValueError(
                "declared basis transform must match the bound path provenance"
            )

    @property
    def direct_basis_transform(self) -> BandPathDirectBasisTransform:
        """Return the exact transform retained by the bound path provenance."""
        provenance = self.calculation.path.provenance
        if provenance is None:
            raise RuntimeError("validated binding result lost path provenance")
        return provenance.direct_basis_transform


class SetyawanCurtaroloPathBinder(
    DataObjectActionizer[
        SetyawanCurtaroloPathBindingRequest,
        SetyawanCurtaroloPathBindingResult,
    ]
):
    """Bind one Appendix-A path to an equivalent ordered simulation basis."""

    __slots__ = ()

    def action(
        self,
        *,
        request: SetyawanCurtaroloPathBindingRequest,
    ) -> SetyawanCurtaroloPathBindingResult:
        """Return the correlated binding with structured basis provenance.

        Let ``S`` be the paper-standard primitive basis and ``A`` the basis in
        ``simulation``. Binding requires ``A = U S R``, where ``U`` is an
        integer-unimodular direct-basis transform and ``R`` is a proper
        Cartesian rotation. Reciprocal-fractional path rows consequently obey
        ``q_A = q_S U**T``.
        """
        if type(request) is not SetyawanCurtaroloPathBindingRequest:
            raise TypeError("request must be a SetyawanCurtaroloPathBindingRequest")
        standard = (
            request.definition.lattice.standard_primitive_lattice_vectors_angstrom
        )
        actual = request.simulation.lattice_vectors_angstrom
        if request.direct_basis_transform is None:
            transform_source = SetyawanCurtaroloBasisTransformSource.recovered
            transform = _recover_integer_basis_transform(
                standard=standard,
                actual=actual,
                tolerance=request.lattice_tolerance_angstrom,
            )
        else:
            transform_source = SetyawanCurtaroloBasisTransformSource.declared
            transform = _validated_integer_basis_transform(
                request.direct_basis_transform
            )
            _validate_basis_equivalence_up_to_proper_rotation(
                standard=standard,
                actual=actual,
                direct_basis_transform=transform,
                tolerance=request.lattice_tolerance_angstrom,
            )
        reciprocal_coordinate_transform = _transpose(_float_matrix(transform))
        calculation = PwDftBandsSimulation(
            simulation=request.simulation,
            path=request.definition._path_with_transform(
                reciprocal_coordinate_transform,
                direct_basis_transform=transform,
            ),
        )
        return SetyawanCurtaroloPathBindingResult(
            request=request,
            calculation=calculation,
            basis_transform_source=transform_source,
        )


def _recover_integer_basis_transform(
    *,
    standard: PwMatrix3,
    actual: PwMatrix3,
    tolerance: float,
) -> BandPathDirectBasisTransform:
    """Recover ``U`` in a shared frame, or recognize a pure proper rotation.

    In a shared Cartesian frame, ``A = U S`` and therefore
    ``U = A S**(-1)``.  Rounding is safe only after the reconstructed basis is
    checked against the requested length tolerance.  If no such integer matrix
    is visible, ``U = I`` is tried with the rotation-invariant metric test.  A
    rotated nonidentity transform cannot be recovered uniquely without a
    bounded lattice-reduction convention, so callers must declare it.
    """
    try:
        return _integer_basis_transform_in_shared_frame(
            standard=standard,
            actual=actual,
            tolerance=tolerance,
        )
    except ValueError:
        identity = _IDENTITY_DIRECT_BASIS_TRANSFORM
        try:
            _validate_basis_equivalence_up_to_proper_rotation(
                standard=standard,
                actual=actual,
                direct_basis_transform=identity,
                tolerance=tolerance,
            )
        except ValueError as rotation_error:
            raise ValueError(
                "simulation unit cell is not an integer-unimodular basis of the "
                "declared Setyawan-Curtarolo standard primitive lattice; supply "
                "direct_basis_transform when a nonidentity basis change is "
                "combined with a Cartesian rotation"
            ) from rotation_error
        return identity


def _integer_basis_transform_in_shared_frame(
    *,
    standard: PwMatrix3,
    actual: PwMatrix3,
    tolerance: float,
) -> BandPathDirectBasisTransform:
    """Solve ``U = A S**(-1)`` when ``A`` and ``S`` share Cartesian axes."""
    candidate = _matrix_product(actual, _inverse(standard))
    rounded: BandPathDirectBasisTransform = tuple(
        tuple(int(round(value)) for value in row) for row in candidate
    )  # type: ignore[assignment]
    if abs(_integer_determinant(rounded)) != 1:
        raise ValueError("the recovered direct-basis transform is not unimodular")
    reconstructed = _matrix_product(_float_matrix(rounded), standard)
    maximum_deviation = max(
        abs(actual_value - reconstructed_value)
        for actual_vector, reconstructed_vector in zip(
            actual,
            reconstructed,
            strict=True,
        )
        for actual_value, reconstructed_value in zip(
            actual_vector,
            reconstructed_vector,
            strict=True,
        )
    )
    if maximum_deviation > tolerance:
        raise ValueError(
            "the bases do not share a Cartesian frame: maximum reconstruction "
            f"deviation {maximum_deviation:.12g} angstrom exceeds "
            f"{tolerance:.12g} angstrom"
        )
    return rounded


def _validated_integer_basis_transform(
    value: BandPathDirectBasisTransform,
) -> BandPathDirectBasisTransform:
    """Validate and retain a declared member of ``GL(3, Z)``.

    ``GL(3, Z)`` consists exactly of integer matrices with determinant ``+1``
    or ``-1``.  Such matrices preserve the primitive-cell volume and have an
    integer inverse, so they change a primitive basis without changing its
    translation lattice.
    """
    if type(value) is not tuple or len(value) != 3:
        raise ValueError("direct_basis_transform must contain three rows")
    if any(
        type(row) is not tuple
        or len(row) != 3
        or any(type(component) is not int for component in row)
        for row in value
    ):
        raise ValueError(
            "direct_basis_transform must be a three-by-three tuple of integers"
        )
    if abs(_integer_determinant(value)) != 1:
        raise ValueError("direct_basis_transform must be integer-unimodular")
    return value


def _validate_basis_equivalence_up_to_proper_rotation(
    *,
    standard: PwMatrix3,
    actual: PwMatrix3,
    direct_basis_transform: BandPathDirectBasisTransform,
    tolerance: float,
) -> None:
    """Validate ``A = U S R`` for some proper Cartesian rotation ``R``.

    For row-vector bases, right multiplication rotates every Cartesian vector.
    It leaves all vector lengths and pairwise distances invariant.  The six
    lengths ``|a_i|`` and ``|a_i-a_j|`` determine the symmetric Gram matrix
    because

    ``a_i . a_j = (|a_i|**2 + |a_j|**2 - |a_i-a_j|**2) / 2``.

    Comparing those six values is therefore equivalent to comparing
    ``A A**T`` with ``U S S**T U**T``, while retaining an angstrom-valued
    tolerance.  Equal determinant signs then select ``det(R) = +1`` rather
    than an improper reflection.
    """
    transformed_standard = _matrix_product(
        _float_matrix(direct_basis_transform),
        standard,
    )
    standard_metric = _basis_metric_lengths(transformed_standard)
    actual_metric = _basis_metric_lengths(actual)
    maximum_deviation = max(
        abs(actual_value - standard_value)
        for actual_value, standard_value in zip(
            actual_metric,
            standard_metric,
            strict=True,
        )
    )
    if maximum_deviation > tolerance:
        raise ValueError(
            "declared direct-basis transform does not reproduce the simulation "
            "lattice metric: maximum invariant-length deviation "
            f"{maximum_deviation:.12g} angstrom exceeds "
            f"{tolerance:.12g} angstrom"
        )
    if _determinant(actual) * _determinant(transformed_standard) <= 0.0:
        raise ValueError(
            "declared direct-basis transform would require an improper Cartesian "
            "reflection rather than a proper rotation"
        )


def _integer_determinant(value: BandPathDirectBasisTransform) -> int:
    return (
        value[0][0] * (value[1][1] * value[2][2] - value[1][2] * value[2][1])
        - value[0][1] * (value[1][0] * value[2][2] - value[1][2] * value[2][0])
        + value[0][2] * (value[1][0] * value[2][1] - value[1][1] * value[2][0])
    )


def _float_matrix(value: BandPathDirectBasisTransform) -> PwMatrix3:
    return tuple(tuple(float(component) for component in row) for row in value)  # type: ignore[return-value]


def _basis_metric_lengths(matrix: PwMatrix3) -> tuple[float, ...]:
    """Return the six rotation-invariant lengths that determine ``A A**T``."""
    a1, a2, a3 = matrix
    return (
        _norm(a1),
        _norm(a2),
        _norm(a3),
        _norm(_subtract(a1, a2)),
        _norm(_subtract(a1, a3)),
        _norm(_subtract(a2, a3)),
    )
