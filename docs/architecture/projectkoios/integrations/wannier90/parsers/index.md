# Parser and record inventory

All public records are frozen, slotted dataclasses. Dense numeric values are
stored by PhysKit as immutable binary64 or complex128 NumPy arrays.

| Native artifact | Parser | Record | Preserved structure |
| --- | --- | --- | --- |
| `.eig` | `Wannier90EigenvalueParser` | `Wannier90EigenvalueData` | one-based indexed complete table |
| `.amn` | `Wannier90ProjectionParser` | `Wannier90ProjectionData` | declared dimensions and ordered k-point matrices |
| `.mmn` | `Wannier90NeighborOverlapParser` | `Wannier90NeighborOverlapData` | neighbor headers, reciprocal shifts, column-major matrix entries |
| `.nnkp` | `Wannier90NeighborListParser` | `Wannier90NeighborListData` | one-based native record order and grouping |
| `.wout` | `Wannier90LocalizationParser` | `Wannier90LocalizationData` | final centers, spreads, Omega labels, maximum converged iteration |
| `_u.mat` | `Wannier90UnitaryMatrixParser` | `Wannier90UnitaryMatrixData` | fractional k-point order and column-major matrices |
| `_hr.dat` | `Wannier90HamiltonianBlockParser` | `Wannier90HamiltonianBlockData` | representative order, degeneracies, indexed complex blocks |

Energy and length units are explicit caller-supplied `ModelSystemUnit` values;
unitless native matrices use `Unitless`. The parsers do not infer, convert, or
normalize units. Floating-point adaptation preserves the donor's binary64 and
complex128 semantics, including input order where the format carries order.

Malformed UTF-8, invalid headers, duplicate or out-of-range indices, incomplete
inventories, truncated matrices, and unexpected trailing content are rejected.
