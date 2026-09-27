# Parser and record inventory

All public records are frozen, slotted dataclasses. Dense numeric values are
stored by PhysKit as immutable binary64 or complex128 NumPy arrays.

| Native artifact | Parser | Record | Preserved structure |
| --- | --- | --- | --- |
| `.eig` | `Wannier90EigenvalueParser` | `Wannier90EigenvalueData` | one-based complete table in mandatory native band/k-point record order |
| `.amn` | `Wannier90ProjectionParser` | `Wannier90ProjectionData` | `(band_count, projection_count)` matrices at ordered k points |
| `.mmn` | `Wannier90NeighborOverlapParser` | `Wannier90NeighborOverlapData` | neighbor headers, reciprocal shifts, column-major matrix entries |
| `.nnkp` | `Wannier90NeighborListParser` | `Wannier90NeighborListData` | one-based native record order and grouping |
| `.wout` | `Wannier90LocalizationParser` | `Wannier90LocalizationData` | final centers/spreads, standard Omega labels, source unit label, reported iterations, and a consistent one-based WF inventory across every reported iteration and the final state |
| `_u.mat` | `Wannier90UnitaryMatrixParser` | `Wannier90UnitaryMatrixData` | fractional k-point order and square `(num_wann, num_wann)` matrices |
| `_hr.dat` | `Wannier90HamiltonianBlockParser` | `Wannier90HamiltonianBlockData` | representative order, degeneracies, indexed complex blocks |

Energy units are explicit caller-supplied `ModelSystemUnit` values. WOUT length
labels `Ang` and `Bohr` are retained and must agree with the caller unit; no
conversion is performed. Unitless native matrices use `Unitless`. One shared
finite Fortran-real tokenizer accepts `E/e` and `D/d` exponents.

`_u_dis.mat` is deliberately unsupported: rectangular disentanglement matrices
are never interpreted as `_u.mat`. Selective-localization `Omega IOD`,
`Omega Rest`, and `_C` variants are also rejected rather than misrepresented.

Malformed UTF-8, invalid headers, duplicate/out-of-range indices, incomplete or
contradictory inventories, truncated matrices, and trailing content are
rejected. In particular, every reported `.wout` iteration must contain the same
ordered one-based WF inventory as the final state. `Wannier90ParserLimits`
defaults to 64 MiB per payload, 1,000,000 per individual dimension, and
10,000,000 numeric records. Checked products and
actual record cardinality are validated before NumPy allocation; callers may
supply stricter positive limits to any parser.
