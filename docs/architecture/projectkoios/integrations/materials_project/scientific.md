# Materials Project elemental-reference scientific qualification

## Purpose

The integration uses a one-element pymatgen convex hull to select an explicit
calculated elemental phase from one retained Materials Project candidate set.
This is a phase-selection aid, not a direct chemical potential for locally
calculated defect energies.

## Hull meaning

For a declared thermodynamic compatibility scheme, pymatgen constructs a phase
diagram from the returned compatible entries and exposes elemental references
through `PhaseDiagram.el_refs`. Pymatgen's phase-diagram facilities and the
Materials Project methodology are described by Ong *et al.* and Jain *et al.*
[1, 2].

The selected entry is qualified by:

- retained candidate set;
- requested compatibility types;
- database state observed at retrieval;
- entry corrections and adjustments represented in the snapshot; and
- pymatgen version and hull implementation.

The result is not an experimental standard state, finite-temperature phase
selection, universal ground-state proof, or guarantee that every allotrope is
present in the database.

## Separation from local energies

Materials Project energies are produced by the database's calculation and
compatibility methodology. They are not subtracted from local QE, VASP, or
other model energies in one formation-energy equation.

The selected phase's exact structure becomes a candidate local input. A
compatible local relaxation and final energy calculation supplies the chemical
potential used with local defect and pristine energies.

## Reproducibility qualification

A retained response snapshot makes the observed candidate set and selected
entry auditable. When Materials Project supplies no immutable database revision,
the snapshot does not prove that repeating the query later will return the same
set. Documentation and provenance must use “retained response snapshot” rather
than “reproducible database revision” in that case.

## References

1. S. P. Ong *et al.*, “Python Materials Genomics (pymatgen): A robust,
   open-source Python library for materials analysis,” *Computational Materials
   Science* **68**, 314–319 (2013),
   [doi:10.1016/j.commatsci.2012.10.028](https://doi.org/10.1016/j.commatsci.2012.10.028).
2. A. Jain *et al.*, “Commentary: The Materials Project: A materials genome
   approach to accelerating materials innovation,” *APL Materials* **1**,
   011002 (2013),
   [doi:10.1063/1.4812323](https://doi.org/10.1063/1.4812323).
