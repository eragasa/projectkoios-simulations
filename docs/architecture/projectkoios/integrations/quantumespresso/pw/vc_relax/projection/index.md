# `vc_relax.projection`

`QeVcRelaxInputProjector` projects a variable-cell relaxation into one QE input
with both `&IONS` and `&CELL` namelists.

The ionic optimizer comes from `[ionic_relaxation].dynamics` and is written as
`&IONS: ion_dynamics`. The lattice-vector optimizer comes from
`[lattice_vector_relaxation].dynamics` and is written as
`&CELL: cell_dynamics`.

Before rendering, the projector validates pressure settings, cell constraints,
and the relationship between the two optimizers. It accepts BFGS for both
namelists, or damped ionic motion paired with either `damp-pr` or `damp-w` cell
motion. It rejects ionic `fire` and every unmatched combination.

The complete TOML-to-QE mapping, native input examples, value constraints, and
validation stages are documented under
[`relaxation.options`](../../relaxation/options/index.md).
