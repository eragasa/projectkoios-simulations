"""Documented three-dimensional algebra for the 2010 convention.

Matrices contain vectors as rows.  Direct bases are measured in angstrom;
reciprocal bases returned here omit ``2*pi`` because that scalar does not
affect fractional coordinates, reciprocal angles, or basis changes.
"""

import math

from projectkoios.simulations.dft.pw.bands import BandVector3
from projectkoios.simulations.dft.pw.simulation import PwMatrix3


def _identity_matrix() -> PwMatrix3:
    """Return the multiplicative identity ``I`` for three-dimensional rows."""
    return ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def _transpose(matrix: PwMatrix3) -> PwMatrix3:
    """Return ``A**T``, exchanging matrix row and column indices."""
    return (
        (matrix[0][0], matrix[1][0], matrix[2][0]),
        (matrix[0][1], matrix[1][1], matrix[2][1]),
        (matrix[0][2], matrix[1][2], matrix[2][2]),
    )


def _matrix_product(first: PwMatrix3, second: PwMatrix3) -> PwMatrix3:
    """Return the matrix product whose entries are row-column dot products."""
    columns = _transpose(second)
    return tuple(tuple(_dot(row, column) for column in columns) for row in first)  # type: ignore[return-value]


def _row_vector_matrix_product(
    vector: BandVector3,
    matrix: PwMatrix3,
) -> BandVector3:
    """Return ``q A`` for a row vector ``q`` and row-major matrix ``A``."""
    columns = _transpose(matrix)
    return (
        _dot(vector, columns[0]),
        _dot(vector, columns[1]),
        _dot(vector, columns[2]),
    )


def _inverse(matrix: PwMatrix3) -> PwMatrix3:
    """Return ``A**(-1)`` from the three-dimensional cofactor formula."""
    determinant = _determinant(matrix)
    if abs(determinant) <= 0.0:
        raise ValueError("matrix must be invertible")
    a, b, c = matrix
    return (
        (
            (b[1] * c[2] - b[2] * c[1]) / determinant,
            (a[2] * c[1] - a[1] * c[2]) / determinant,
            (a[1] * b[2] - a[2] * b[1]) / determinant,
        ),
        (
            (b[2] * c[0] - b[0] * c[2]) / determinant,
            (a[0] * c[2] - a[2] * c[0]) / determinant,
            (a[2] * b[0] - a[0] * b[2]) / determinant,
        ),
        (
            (b[0] * c[1] - b[1] * c[0]) / determinant,
            (a[1] * c[0] - a[0] * c[1]) / determinant,
            (a[0] * b[1] - a[1] * b[0]) / determinant,
        ),
    )


def _determinant(matrix: PwMatrix3) -> float:
    """Return the oriented volume ``a1 . (a2 x a3)`` of three row vectors."""
    a, b, c = matrix
    return _dot(a, _cross(b, c))


def _reciprocal_vectors(matrix: PwMatrix3) -> PwMatrix3:
    """Return reciprocal rows ``A**(-T)`` without the conventional ``2*pi``."""
    a1, a2, a3 = matrix
    volume = _determinant(matrix)
    if abs(volume) <= 0.0:
        raise ValueError("lattice must have nonzero volume")
    return (
        _scale(_cross(a2, a3), 1.0 / volume),
        _scale(_cross(a3, a1), 1.0 / volume),
        _scale(_cross(a1, a2), 1.0 / volume),
    )


def _angle_degrees(first: BandVector3, second: BandVector3) -> float:
    """Return ``acos((u.v)/(|u||v|))`` in degrees, clipping roundoff."""
    cosine = _dot(first, second) / math.sqrt(_dot(first, first) * _dot(second, second))
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def _cross(first: BandVector3, second: BandVector3) -> BandVector3:
    """Return the right-handed Cartesian cross product ``first x second``."""
    return (
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    )


def _dot(first: BandVector3, second: BandVector3) -> float:
    """Return the Euclidean scalar product ``sum(first_i * second_i)``."""
    return sum(x * y for x, y in zip(first, second, strict=True))


def _subtract(first: BandVector3, second: BandVector3) -> BandVector3:
    """Subtract Cartesian row vectors component by component."""
    return (
        first[0] - second[0],
        first[1] - second[1],
        first[2] - second[2],
    )


def _norm(vector: BandVector3) -> float:
    """Return the Euclidean length ``sqrt(v . v)`` of a Cartesian vector."""
    return math.sqrt(_dot(vector, vector))


def _scale(vector: BandVector3, factor: float) -> BandVector3:
    """Multiply every Cartesian component by one scalar."""
    return tuple(value * factor for value in vector)  # type: ignore[return-value]
