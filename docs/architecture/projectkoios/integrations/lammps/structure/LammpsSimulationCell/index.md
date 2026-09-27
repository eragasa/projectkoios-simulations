# `LammpsSimulationCell`

**Implemented in:** `projectkoios.integrations.lammps.structure`

Immutable simulation-cell input.

- `scale` is finite and strictly positive.
- `lattice` contains exactly three finite three-component vectors.
- `atoms` is nonempty and contains at most 10,000,000 entries.

The class accepts general finite matrices as data, while `render_lammps_data`
currently rejects off-diagonal terms because the retained historical
transformation is inconsistent for triclinic cells.
