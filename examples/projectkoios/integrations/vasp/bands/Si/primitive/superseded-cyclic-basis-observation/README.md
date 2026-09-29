# VASP 5.3.5 silicon bands software observation

This directory retains the exact non-self-consistent line-mode input bytes from
one explicitly authorized local VASP 5.3.5 software-integration run. Tests and
normal example use must not execute these files.

> **Superseded:** the run used a cyclic permutation of the canonical
> `Si.primitive` lattice-vector order while retaining untransformed fractional
> path coordinates. Cubic symmetry makes the sampled path symmetry-equivalent,
> but this evidence does not establish projection from the exact canonical
> structure definition. It must not be used as the canonical reference run.

## Purpose

The run exercised the maintained data route:

```text
converged parent CHGCAR
  -> VASP ICHARG=11 line-mode run
  -> vasprun.xml plus independent OUTCAR/execution evidence
  -> VaspBandDataExtractor
  -> BandDiagramData
  -> application-owned SVG
```

No VASP plotting tool is part of the extraction route.

## Path and sample count

The path follows the VASP Wiki fcc-silicon example:

```text
L - Gamma - X - U | K - Gamma
```

VASP line mode includes both endpoints of every segment. Four segments with 20
points each therefore produce 80 XML samples. Shared interior vertices are
repeated according to VASP's documented native semantics. The `U | K` boundary
is a discontinuity, not a segment.

## Retention policy

The small INCAR, KPOINTS, and POSCAR files are copied here. The licensed POTCAR,
parent CHGCAR, OUTCAR, `vasprun.xml`, and captured streams are not redistributed;
`manifest.json` records their path-at-execution, byte count, and SHA-256
identity. Presentation-product identities are recorded independently.

The recorded authorization applied only to the historical run. Neither the
inputs nor the manifest grant authority to execute VASP again.

## Nonclaims

This evidence demonstrates that the provider software path completed and that
independent VASP sources mechanically agreed with the declared line path. It
does not establish cutoff, SCF-mesh, path-sampling, band-count, or
pseudopotential convergence; physical accuracy; agreement with experiment; or
scientific validation.
