# Canonical VASP 5.3.5 silicon bands software observation

This directory retains the exact non-self-consistent line-mode input bytes from
one explicitly authorized local VASP 5.3.5 software-integration run. Its parent
SCF run and band run both used the canonical neutral `Si.primitive`
lattice-vector order. Tests and normal example use must not execute these files.

## Maintained route

```text
canonical Si.primitive UnitCell
  -> PwDftSimulation
  -> PwDftBandsSimulation + reciprocal-fractional BandPath
  -> VASP SCF and retained CHGCAR
  -> VASP ICHARG=11 line-mode run with derived Reciprocal KPOINTS
  -> vasprun.xml plus independent OUTCAR/execution evidence
  -> configured UnitCell and vasprun.xml structure agreement
  -> VaspBandDataExtractor
  -> BandDiagramData
  -> application-owned SVG
```

No VASP plotting tool is part of the extraction route.

## Structure and path

The source structure is the identity-bound
`examples/projectkoios/simulations/dft/pw/Si/primitive/Si.primitive.json`.
The path follows the VASP Wiki fcc-silicon example:

```text
L - Gamma - X - U | K - Gamma
```

VASP line mode includes both endpoints of every segment. Four segments with 20
points each therefore produce 80 XML samples. Shared interior vertices are
repeated according to VASP's native semantics. The `U | K` boundary is a
discontinuity, not a segment.

## Retention and authorization

The small INCAR, KPOINTS, and POSCAR files are copied here. The licensed POTCAR,
parent SCF evidence and CHGCAR, OUTCAR, `vasprun.xml`, and captured streams are
not redistributed; `manifest.json` records their byte counts and SHA-256
identities. Presentation-product identities are recorded independently.

The recorded authorization applied only to these historical executions.
Neither the inputs nor the manifest grant authority to execute VASP again.

## Nonclaims

This evidence demonstrates completion of the provider software route, agreement
between the configured and XML unit cells, and mechanical agreement between XML
k-points and the declared line path. It does not establish cutoff, SCF-mesh,
path-sampling, band-count, or pseudopotential convergence; physical accuracy;
agreement with experiment; or scientific validation.
