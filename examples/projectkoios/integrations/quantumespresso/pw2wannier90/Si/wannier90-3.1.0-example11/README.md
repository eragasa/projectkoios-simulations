# Wannier90 3.1.0 example11: silicon interface inputs

This directory retains the four original, unmodified simulation input files from
Wannier90 3.1.0 `examples/example11`. The source example represents the complete
five-stage route:

1. Quantum ESPRESSO SCF;
2. Quantum ESPRESSO uniform-grid NSCF;
3. `wannier90.x -pp silicon` preprocessing;
4. `pw2wannier90.x`; and
5. `wannier90.x silicon` localization.

## Provenance

- Upstream project: [Wannier90](https://github.com/wannier-developers/wannier90)
- Upstream release: `3.1.0`
- Source directory: `wannier90-3.1.0/examples/example11`
- Source archive: `wannier90-3.1.0.tar.gz`
- Source archive SHA-256:
  `40651a9832eb93dec20a8360dd535262c261c34e13c41b6755fa6915c936b254`
- Source-directory path-and-content manifest SHA-256:
  `29a2acef7afedb57b5fad1f84bd6cbe372741788a16e01a99cf9166207038ad2`
- Project inventory context: `ksdft2effmass` commit
  `7bd913151f7e61ed2bdba593df920be36573b502`
- Inventory document:
  `docs/computational/wannier90.tutorials.v3_1_0.md`
- Source task record:
  `tasks/simulation/wannier90.tutorials.v3_1_0.example11.json`

Exact per-file identities and context-document Git blobs are recorded in
[`source.toml`](source.toml) and the repository-level `TRANSFER.toml`. A second,
byte-identical materialization of `silicon.nscf` is retained as the stage-local
`pw/nscf/Si/primitive/input/pw.in` example.

## Boundaries

These files are retained as citation-bound, non-code simulation inputs. They
have not been modified, rendered, or executed by this repository. The referenced
`Si.pbe-n-van.UPF` pseudopotential is not included. QE saved state, `.nnkp`,
interface outputs, Wannier90 outputs, and numerical or scientific acceptance are
also not included.

Possession of these inputs does not authorize calculator execution or establish
convergence, interface compatibility, localization, numerical verification, or
scientific validation.
