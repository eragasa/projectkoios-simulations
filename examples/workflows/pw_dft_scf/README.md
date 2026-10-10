# Plane-wave DFT SCF examples

## Campaigns

`campaigns/` contains a compact matrix for silicon's primitive cell:

| Integration | Single | K-point | Cutoff | Joint grid |
| --- | --- | --- | --- | --- |
| Quantum ESPRESSO | `qe-single.toml` | `qe-kpoint.toml` | `qe-cutoff.toml` | `qe-grid.toml` |
| VASP | `vasp-single.toml` | `vasp-kpoint.toml` | `vasp-cutoff.toml` | `vasp-grid.toml` |

The TOML documents select stable integration, structure, sampling, coordinate,
policy, and projection-profile identities. They do not identify executables or
carry execution authority.

## Comparisons and structures

`comparisons/` contains the single-SCF and three convergence comparisons.
Relative campaign paths resolve within this directory. `structures/catalog.toml`
is the exact manifest-backed structure library used by the tools configuration.
It records the representation, schema version, byte size, SHA-256, and immutable
transfer provenance of each reviewed cell.

`structures/silicon_substitutional_defects.py` resolves the exact conventional
silicon cell, constructs its `(2, 2, 2)` pristine supercell, and declares neutral
unrelaxed Si:P and Si:B deltas at original supercell atom index `0`. The
example applies those deltas mechanically. It does not choose a scientifically
appropriate defect model, infer a relaxed structure, or authorize calculator
execution.

`replay_normalized_evidence.py` demonstrates the pure convergence replay action
against already normalized evidence. It performs no provider parsing or
calculator execution.

Use the commands described in `tools/pw_dft_scf/README.md` to load, project,
plan, replay, compare, or visualize these declarations.
