# Calculator-neutral structure contracts

`projectkoios.simulations.structure` owns calculator-neutral contracts for exact
stored unit cells, derived supercells, and ideal defect deltas. It builds on the
canonical PhysKit hierarchy: `UnitCell`, `PrimitiveUnitCell`, and
`ConventionalUnitCell`. It does not duplicate those cell types.

## Contents

- [`library`](library/index.md) binds stable structure identifiers to immutable
  bytes, schema versions, representations, and transfer provenance.
- [`supercell`](supercell/index.md) derives a `SuperCell(UnitCell)` while
  retaining source-site provenance.
- [`defect`](defect/index.md) declares vacancies, interstitials,
  substitutions, and complexes through one generic `UnitCellDefectDelta`.

## Boundaries

Structure records and transformations do not select a calculator, executable,
pseudopotential, convergence policy, charge-compensation method, relaxation
method, or scientifically acceptable model. Loading, verifying, constructing,
and applying a delta are deterministic in-process data operations. They grant
no calculator execution authority.

The structure library stores only the primitive and conventional
representations supported by PhysKit's version-one deterministic JSON codec.
A `SuperCell` and a defect result are derived `UnitCell` values. They are not
silently relabeled as primitive, conventional, or relaxed structures.
