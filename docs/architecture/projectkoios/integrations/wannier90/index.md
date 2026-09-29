# `projectkoios.integrations.wannier90`

## Ownership

This outward integration owns execution-independent adaptation of seven
caller-supplied Wannier90 text artifacts:

- `.eig` indexed eigenvalues
- `.amn` projections
- `.mmn` neighbor-overlap matrices
- `.nnkp` neighbor lists
- `.wout` final localization observations
- `_u.mat` gauge matrices
- `_hr.dat` real-space Hamiltonian blocks

The package has no filesystem discovery, subprocess, calculator, workflow,
interpolation, convergence-policy, or scientific-acceptance behavior.

## Dependency direction

```text
projectkoios.integrations.wannier90
    -> projectkoios.physkit.units.quantities
    -> NumPy/Pint/SciPy (through projectkoios-physkit)

projectkoios.simulations -X-> projectkoios.integrations
```

Native parser records are integration-owned. The inward
`projectkoios.simulations` namespace must never import them. No new neutral
simulation record was identified during extraction.

## Public surfaces

- [Artifact identity and set correlation](artifacts/index.md)
- [Parser and record inventory](parsers/index.md)
- [Provenance and scientific limits](provenance/index.md)
