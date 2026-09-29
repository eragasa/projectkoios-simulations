# Silicon uniform-grid NSCF input

This directory provides the Quantum ESPRESSO NSCF stage from the original
Wannier90 3.1.0 `examples/example11` silicon workflow. The retained `input/pw.in`
is a byte-for-byte copy of upstream `silicon.nscf`.

The original workflow uses this 64-point uniform `4 × 4 × 4` grid after its SCF
stage and before `wannier90.x -pp silicon`, `pw2wannier90.x`, and
`wannier90.x silicon`.

## Provenance

- Upstream project: [Wannier90](https://github.com/wannier-developers/wannier90)
- Release: `3.1.0`
- Source path: `wannier90-3.1.0/examples/example11/silicon.nscf`
- Source archive SHA-256:
  `40651a9832eb93dec20a8360dd535262c261c34e13c41b6755fa6915c936b254`
- Input SHA-256:
  `6bfe71900d579edc2fddae0b2a9da65dc7bc6f28ff77eef819569ed174fccd42`
- Inventory context: `ksdft2effmass` commit
  `7bd913151f7e61ed2bdba593df920be36573b502`

The complete upstream four-file input set and its provenance record are retained
under
`../../../../pw2wannier90/Si/wannier90-3.1.0-example11/`.

## Maintained configuration

The implemented NSCF loader requires one closed-schema TOML configuration that
contains all source-input, structure, `pw.x`, pseudopotential, parent-SCF,
output, and optional reference-output paths together with byte sizes and
SHA-256 identities. Relative paths are resolved against the configuration file.
The configuration is extracted into immutable typed records, an NSCF control
block, and common QE `pw.x` cards before rendering.

[`calculation.template.toml`](calculation.template.toml) records the complete
schema and the identities already known. Its `/replace/with/` paths and all-zero
parent-manifest identity are explicit placeholders; the template is not a
runnable calculation declaration. A materialized configuration must replace
every placeholder with the matching SCF output, saved-state manifest, local
resource paths, and observed identities. An unrelated SCF state must not be
substituted silently. Configuration content cannot grant calculator-execution
authority.

## Boundaries

This is a citation-bound, non-code simulation input. The referenced
`Si.pbe-n-van.UPF` pseudopotential and QE saved state are not included. The input
has not been executed by this repository and does not establish convergence,
interface compatibility, numerical verification, or scientific validation.
Calculator execution requires separate explicit authorization.
