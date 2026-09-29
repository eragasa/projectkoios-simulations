# Canonical QE 7.5 silicon bands software observation

This directory retains the exact SCF and bands input bytes from one explicitly
authorized local Quantum ESPRESSO 7.5 software-integration run. Both phases were
projected from the canonical neutral `Si.primitive` lattice-vector order. Tests
and normal example use must not execute these files.

## Maintained route

```text
canonical Si.primitive UnitCell
  -> PwDftSimulation
  -> PwDftBandsSimulation + reciprocal-fractional BandPath
  -> pw.x SCF saved state
  -> pw.x calculation='bands' with derived K_POINTS crystal_b
  -> data-file-schema.xml
  -> parsed QEXSD document
  -> configured UnitCell and QEXSD UnitCell agreement
  -> QeBandsDataExtractor
  -> BandDiagramData
  -> application-owned SVG
```

The extraction did not consume `bands.x`, `plotband.x`, or
`*.bands.dat.gnu`. QEXSD is the authoritative structured numerical source.

## Structure and path

The source structure is the identity-bound
`examples/projectkoios/simulations/dft/pw/Si/primitive/Si.primitive.json`.
The path has two branches:

```text
L - Gamma - X - U | K - Gamma
```

With 20 QE `crystal_b` interpolation points per segment, the first branch has 61
samples and the second has 21, for 82 total. The `U | K` boundary is a
reciprocal-space discontinuity.

## Retention and authorization

Only the small input files are copied here. `manifest.json` records byte counts
and SHA-256 identities for the structure, executable, pseudopotential, stdout,
QEXSD, saved charge density, and presentation products. External artifacts are
not silently represented as repository files.

The recorded authorization applied only to these historical executions.
Neither the inputs nor the manifest grant authority to execute a calculator
again.

## Nonclaims

This evidence demonstrates completion of the software route, agreement between
the configured and QEXSD unit cells, and mechanical agreement between QEXSD
k-points and the declared path. It does not establish cutoff, SCF-mesh,
band-count, or pseudopotential convergence; band connectivity; physical
accuracy; agreement with experiment; or scientific validation.
