# Calculator-neutral `Si.primitive`

This directory is the shared structure boundary for the maintained silicon
plane-wave examples.

`Si.primitive.json` defines one exact right-handed primitive-cell basis:

```text
a1 = (2.715, 2.715, 0.000) angstrom
a2 = (0.000, 2.715, 2.715) angstrom
a3 = (2.715, 0.000, 2.715) angstrom
```

Two path declarations retain distinct published conventions:

- `Si.primitive.fcc-band-path.json` retains the shorter VASP Wiki path used by
  the existing authorized software observations;
- `Si.primitive.setyawan-curtarolo-2010-band-path.json` retains the complete FCC
  path from Setyawan and Curtarolo, DOI
  `10.1016/j.commatsci.2010.05.010`.

Both declare fractional reciprocal coordinates against this exact ordered
basis and bind its SHA-256 identity. The local basis is the cyclic ordering
`(a3, a1, a2)` of the paper's FCC standard primitive basis. The
Setyawan--Curtarolo declaration therefore records that integer-unimodular basis
transformation and the corresponding transformed reciprocal coordinates. Its
schema-version-2 `provenance` object mirrors `BandPathConventionProvenance`,
including the convention revision, DOI, Bravais identity, Appendix-A case, and exact
direct-basis transform.
Changing the lattice requires a new binding or another explicit coordinate
transformation.

At runtime the structure is loaded into `PwDftSimulation.unit_cell`.
`PwDftBandsSimulation` composes that simulation with the declared path. QE and
VASP adapters receive the composed record and derive `K_POINTS crystal_b` or
VASP reciprocal line mode; they do not own another copy of the lattice.

The files are inert declarations. They grant no calculator-execution
authorization and make no convergence or scientific-validation claim.
