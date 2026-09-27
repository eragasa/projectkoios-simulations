# `QeIbrav`

Immutable validated QE Bravais-lattice declaration with `ibrav`, `space_group`, `celldm`, `lattice_parameters`, and `cell_parameters` fields.

- `ibrav` may be omitted only when `space_group` is present.
- `ibrav = 0` requires `CELL_PARAMETERS` and permits either no separate lattice parameter, only `celldm(1)`, or only `A`.
- Nonzero `ibrav` forbids `CELL_PARAMETERS`, requires exactly one parameter family (`celldm` or `A, B, C, cosAB, cosAC, cosBC`), and enforces the exact shape parameters required by that `ibrav` identity.
- The two parameter families are mutually exclusive.
