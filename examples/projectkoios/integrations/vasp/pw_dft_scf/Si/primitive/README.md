# Silicon VASP single-SCF integration

This directory retains a static VASP-native projection for a primitive-silicon
SCF calculation. The rendered `INCAR`, `KPOINTS`, `POSCAR`, and
`input-projection.json` files are inspection examples; this repository does not
include an application runner that regenerates or executes them.

The retained
[`negative-lattice-orientation`](evidence/failures/negative-lattice-orientation/README.md)
failure demonstrates that a zero process return code does not imply calculator
or workflow success. It is failure evidence, not a successful reference result,
numerical verification, or scientific validation.

`campaign.toml` preserves the calculator and projection declaration associated
with these artifacts. It does not grant calculator-execution authority.
