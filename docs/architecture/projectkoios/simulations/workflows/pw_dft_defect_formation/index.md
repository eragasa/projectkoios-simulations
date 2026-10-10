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

The committed catalog contains exact topology fixtures for the ideal cells, but
production supercells are rebuilt from one locally optimized zero-pressure Si
host. For every defect and size, the primary study declares ideal, `<100>`, and
`<111>` symmetry-broken starts, fixed-host ion relaxation, and a compatible
final SCF. Optional full-cell runs are separately labeled finite-concentration
strain diagnostics. Every neutral Si:P and Si:B stage is explicitly
spin-polarized as a doublet and disables spatial and time-reversal symmetry
reductions; it cannot reuse the unpolarized bulk-silicon profile.

The study also requires compatible local relaxation and final-SCF
specifications for diamond silicon and the retained B `mp-160` and P
`mp-568348` phases selected by authenticated Materials Project hull queries.
Their database energies are not used as local chemical potentials.

## Composition stages

The target composition is:

1. resolve the exact relaxed host structure and derive each pristine supercell;
2. create each ideal defect by changing only the declared host-site species,
   preserving the host-supercell lattice parameters and atomic positions;
3. derive exact ideal, `<100>`, and `<111>` starting cells and disable spatial
   and time-reversal symmetry reductions;
4. obtain or request `ATOMIC_POSITIONS` relaxation evidence for each start and
   publish ion-relaxed structures after verifying that each lattice is fixed;
5. obtain or request separate final SCFs and retain the lowest compatible
   converged observed basin without claiming a proven global minimum;
6. retain the residual stress tensor for the fixed-host size series;
7. optionally obtain pressure-qualified `ATOMIC_POSITIONS_AND_CELL` diagnostics;
8. qualify pristine, defect, and elemental-reference evidence;
9. derive local elemental chemical potentials and neutral substitution
   formation energies; and
10. compare matched 64-, 216-, and 512-atom observations under explicit
    workflow-owned formation-energy and residual-stress policies.

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
