# `LammpsAtom`

**Implemented in:** `projectkoios.integrations.lammps.structure`

Immutable atom input for deterministic data rendering.

- `symbol` must match an uppercase chemical-style symbol with up to two
  lowercase letters.
- `fractional_position` must contain exactly three finite floats.
- `charge` is optional for atomic style and must be finite when present; charge
  style requires it for every atom.

The model stores explicit input only and performs no species lookup or unit
conversion.
