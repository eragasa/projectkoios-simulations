# `projectkoios.integrations.lammps.structure`

**Source:** `.../integrations/lammps/structure.py`

Deterministic, effect-free LAMMPS data-file rendering.

## Types

- `Vector3 = tuple[float, float, float]`
- `Matrix3 = tuple[Vector3, Vector3, Vector3]`
- `AtomStyle = Literal["atomic", "charge"]`

## Classes

- [`LammpsAtom`](LammpsAtom/index.md)
- [`LammpsSimulationCell`](LammpsSimulationCell/index.md)
- [`LammpsDataArtifact`](LammpsDataArtifact/index.md)

## `render_lammps_data(...)`

Requires an exact species order covering all atoms, a supported atom style, and
explicit charges for charge-style output. Because retained source handles
triclinic coordinates inconsistently, only diagonal finite positive cells are
accepted. Atoms are grouped by explicit species order, coordinates are derived
from fractional positions, and output uses deterministic four-decimal text.

The function returns an in-memory artifact. It does not write files or invoke a
calculator. Internal helpers validate species coverage, symbols, and finite
three-component vectors. Bounds permit at most 10,000,000 atoms and at most
1,000,000,000 serialized bytes.
