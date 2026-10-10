# Plane-wave DFT defect-formation workflow capability

## Status

This node specifies a target owner-specific workflow capability. The production
`projectkoios.simulations.workflows.pw_dft_defect_formation` package, workflow
definition, and Petri net do not yet exist. The documentation does not displace
the current SCF Petri-net authority, which remains the sole executable
simulation-workflow topology in this repository.

## Purpose

The capability will compose exact structure and simulation records, existing
SCF and relaxation workflows, immutable execution evidence, chemical-potential
derivation, formation-energy calculation, and supercell-size assessment into a
provider-independent study.

It owns scientific study composition and acceptance policy. It does not own
provider syntax, parser implementations, calculator execution, durable runtime
state, or credentials.

## Initial study matrix

The first declared study contains a matched 64-, 216-, and 512-atom series of
pristine, substitutional-phosphorus, and substitutional-boron silicon cells at
three conventional-cell replication sizes:

| Replication | Pristine atoms | Defect declarations |
| --- | ---: | --- |
| `(2, 2, 2)` | 64 | `Si:P`, `Si:B` |
| `(3, 3, 3)` | 216 | `Si:P`, `Si:B` |
| `(4, 4, 4)` | 512 | `Si:P`, `Si:B` |

For every defect and supercell size, the study declares an ideal host-geometry
cell, an ion-only fixed-cell relaxation, and a full ion-and-cell relaxation.
Each resulting geometry receives a compatible final SCF so the ion-only and
fully relaxed energies can be compared as the cell-strain contribution without
using optimizer-step energies. Every neutral Si:P stage is explicitly
spin-polarized as a doublet; it cannot reuse the non-spin-polarized bulk-silicon
profile.

The study also requires compatible local relaxation and final-SCF
specifications for diamond silicon and the actual boron and phosphorus phases
selected by the injected Materials Project integration. Selected phase IDs
cannot be hard-coded before the authenticated hull query is performed and
retained.

## Composition stages

The target composition is:

1. resolve the exact relaxed host structure and derive each pristine supercell;
2. create each ideal defect by changing only the declared host-site species,
   preserving the host-supercell lattice parameters and atomic positions;
3. obtain or request `ATOMIC_POSITIONS` relaxation evidence and publish the
   ion-relaxed structure after verifying that its lattice remains fixed;
4. initialize `ATOMIC_POSITIONS_AND_CELL` relaxation from the ion-relaxed
   structure, obtain or request its evidence, and publish the fully relaxed
   structure with pressure qualification;
5. obtain or request a separate final SCF for the ideal, ion-relaxed, and fully
   relaxed structures under one qualified energy model;
6. qualify pristine, defect, and elemental-reference evidence;
7. derive local elemental chemical potentials and neutral substitution
   formation energies;
8. derive ionic, cell-strain, and total relaxation energies, including
   `E_ion_only - E_fully_relaxed` at zero external pressure;
9. compare matched 64-, 216-, and 512-atom observations; and
10. apply explicit workflow-owned formation-energy and strain-energy acceptance
    policies.

Every calculation handoff remains non-authorizing. Missing evidence produces a
typed requirement or handoff, not implicit execution.

## Reuse of existing workflows

The new package composes public contracts from `pw_dft_relaxation` and
`pw_dft_scf`; it does not duplicate their calculator-input translation, SCF
lifecycle, convergence, replay, or result contracts. Calculator selection may
be represented by neutral integration IDs, while actual QE or VASP composition
remains in outward tools or applications.

## Topology status

Documentation does not establish an executable topology. A future workflow
shape may be introduced only after its places, transitions, occurrence
semantics, and extraction boundary are reviewed. Until then, the package should
begin as immutable composition, policy, and decision records rather than a
second partial Petri-net description.

See [`implementation.md`](implementation.md) for package and dependency rules,
[`schematics.md`](schematics.md) for the planned study flow,
[`scientific.md`](scientific.md) for the cited study protocol, and
[`numeric.md`](numeric.md) for size-series and acceptance-policy requirements.
