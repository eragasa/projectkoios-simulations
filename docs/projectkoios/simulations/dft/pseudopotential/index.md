# `projectkoios.simulations.dft.pseudopotential`

Calculator-neutral pseudopotential identity and deployment-resolution package.

## Modules

- `model` defines [`Pseudopotential`](Pseudopotential/index.md),
  `PseudopotentialArtifactFormat`, and
  [`PseudopotentialFile`](PseudopotentialFile/index.md).
- [`library`](library/index.md) locates machine-local files matching complete
  caller-owned `PseudopotentialFile` identities.

Scientific code chooses the complete pseudopotential requirement. The library
only locates and verifies its exact bytes; it does not select by element or
family, download artifacts, or grant calculator authority.
