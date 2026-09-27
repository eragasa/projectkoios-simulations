# `projectkoios.integrations.lammps`

**Source:** `src/python/projectkoios/integrations/lammps/`

Effect-free LAMMPS reconstruction boundary.

> **Status:** reconstruction scaffold. This package does not execute LAMMPS,
> parse calculator results, control convergence, or establish behavioral
> conformance, numerical verification, or scientific validation.

The pinned recovery source has no bounded, maintained LAMMPS example tree. The
historical PyFlamestk and PyPosPack example corpora and separately owned
`ksdft2effmass` smoke evidence are outside this transfer; this scaffold does not
claim a synthetic replacement example.

## Modules

- [`models`](models/index.md) defines protected template and command observations.
- [`inspection`](inspection/index.md) reconstructs those observations from
  verified runner-script text.
- [`provenance`](provenance/index.md) verifies selected files in an explicit
  checkout of the exact external PyPosPack revision.
- [`structure`](structure/index.md) deterministically renders bounded LAMMPS
  data-file text in memory.

The package facade re-exports the public classes, source identity constants,
`inspect_lammps_templates`, `verify_pypospack_lammps_checkout`, and
`render_lammps_data`. None of these APIs invokes LAMMPS or writes a data file.
