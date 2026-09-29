# QE 7.5 silicon bands software observation

This directory retains the exact SCF and bands input bytes from one explicitly
authorized local Quantum ESPRESSO 7.5 software-integration run. Tests and normal
example use must not execute these files.

> **Superseded:** the run used a cyclic permutation of the canonical
> `Si.primitive` lattice-vector order while retaining untransformed fractional
> path coordinates. Cubic symmetry makes the sampled path symmetry-equivalent,
> but this evidence does not establish projection from the exact canonical
> structure definition. It must not be used as the canonical reference run.

## Purpose

The run exercised the maintained data route:

```text
pw.x SCF saved state
  -> pw.x calculation='bands' with K_POINTS crystal_b
  -> data-file-schema.xml
  -> parsed QEXSD document
  -> QeBandsDataExtractor
  -> BandDiagramData
  -> application-owned SVG
```

The final extraction did not consume `bands.x`, `plotband.x`, or
`*.bands.dat.gnu`. The manifest field `gnu_plot_data_consumed` is therefore
false. QEXSD is the authoritative structured numerical source.

## Path and sample count

The declared primitive-cell path has two branches:

```text
L - Gamma - X - U | K - Gamma
```

With 20 QE `crystal_b` interpolation points per segment, the first branch has 61
samples and the second has 21, for 82 total. The `U | K` boundary is a
reciprocal-space discontinuity.

## Retention policy

Only the small input files are copied here. `manifest.json` records byte counts
and SHA-256 identities for the executable, pseudopotential, stdout, QEXSD, saved
charge density, and generated presentation products. The external artifacts are
not silently represented as repository files.

The recorded authorization applied only to the historical run. Neither the
inputs nor the manifest grant authority to execute a calculator again.

## Nonclaims

This evidence demonstrates that the software path completed and that the QEXSD
k-points mechanically matched the declared path. It does not establish cutoff,
k-mesh, band-count, or pseudopotential convergence; band connectivity; physical
accuracy; agreement with experiment; or scientific validation.
