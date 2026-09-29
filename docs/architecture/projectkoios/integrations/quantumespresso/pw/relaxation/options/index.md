# Relaxation options and QE namelists

The calculation configuration groups settings by physical purpose. Quantum
ESPRESSO distributes those settings across three native namelists:

- `&CONTROL` contains stopping thresholds and the maximum number of ionic steps;
- `&IONS` selects the ionic optimizer; and
- `&CELL` selects the lattice-vector optimizer and cell constraints.

The common `QeControlCard`, `QeIonsCard`, and `QeCellCard` objects render these
namelists. They do not choose the options or define scientific policy.

## Ionic relaxation

Both `relax` and `vc-relax` require an `[ionic_relaxation]` table:

```toml
[ionic_relaxation]
dynamics = "bfgs"
maximum_steps = 100
total_energy_tolerance_ry = 1.0e-4
force_tolerance_ry_per_bohr = 1.9446903798e-4
```

Its fields are rendered as follows:

- `dynamics` becomes `ion_dynamics` in `&IONS`;
- `maximum_steps` becomes `nstep` in `&CONTROL`;
- `total_energy_tolerance_ry` becomes `etot_conv_thr` in `&CONTROL`; and
- `force_tolerance_ry_per_bohr` becomes `forc_conv_thr` in `&CONTROL`.

The corresponding native fragments are:

```text
&CONTROL
  nstep = 100
  etot_conv_thr = 1.0000000000e-04
  forc_conv_thr = 1.9446903798e-04
/
&IONS
  ion_dynamics = 'bfgs'
/
```

`maximum_steps` must be a positive integer. Both thresholds must be positive and
finite. The maintained ionic optimizer values are `bfgs`, `damp`, and `fire`,
but `fire` is supported only for fixed-cell `relax` in this adapter.

## Lattice-vector relaxation

Only `vc-relax` accepts—and requires—a `[lattice_vector_relaxation]` table:

```toml
[lattice_vector_relaxation]
dynamics = "bfgs"
degrees_of_freedom = "all"
target_pressure_kbar = 0.0
pressure_tolerance_kbar = 0.5
```

Every field in this table is rendered into `&CELL`:

- `dynamics` becomes `cell_dynamics`;
- `degrees_of_freedom` becomes `cell_dofree` and uses the maintained
  [`QeCellDegreesOfFreedom`](../../inputfile/cell/QeCellDegreesOfFreedom/index.md)
  values;
- `target_pressure_kbar` becomes `press`; and
- `pressure_tolerance_kbar` becomes `press_conv_thr`.

The corresponding native fragment is:

```text
&CELL
  cell_dynamics = 'bfgs'
  press = 0.0000000000
  press_conv_thr = 0.5000000000
  cell_dofree = 'all'
/
```

The target pressure must be finite and the pressure tolerance must be positive
and finite. For the maintained `ibrav = 0` input, `cell_dofree = 'ibrav'` is
invalid. `cell_dynamics = 'none'` does not relax the cell and is rejected.
Quantum ESPRESSO 7.5 documents `cell_dynamics = 'sd'` but does not implement it,
so the adapter rejects that value as well.

## Coupling required by `vc-relax`

For `vc-relax`, the optimizer in `&IONS` must be compatible with the optimizer
in `&CELL`. The adapter accepts exactly these combinations:

1. `ion_dynamics = 'bfgs'` with `cell_dynamics = 'bfgs'`;
2. `ion_dynamics = 'damp'` with `cell_dynamics = 'damp-pr'`; or
3. `ion_dynamics = 'damp'` with `cell_dynamics = 'damp-w'`.

For example, this is valid:

```toml
[ionic_relaxation]
dynamics = "damp"
maximum_steps = 100
total_energy_tolerance_ry = 1.0e-4
force_tolerance_ry_per_bohr = 1.9446903798e-4

[lattice_vector_relaxation]
dynamics = "damp-pr"
degrees_of_freedom = "all"
target_pressure_kbar = 0.0
pressure_tolerance_kbar = 0.5
```

It renders `ion_dynamics = 'damp'` in `&IONS` and
`cell_dynamics = 'damp-pr'` in `&CELL`.

All other combinations are rejected. In particular, ionic `fire` is rejected
for `vc-relax`, `bfgs` cannot be paired with `damp-pr` or `damp-w`, and `damp`
cannot be paired with cell `bfgs`.

## Validation stage

TOML loading validates the table shapes, value types, and numeric bounds. The
calculation record requires ionic options for both modes, rejects
lattice-vector options for fixed-cell `relax`, and requires lattice-vector
options for `vc-relax`.

The relationship between `ion_dynamics` and `cell_dynamics` is checked when the
`vc-relax` input is projected. An incompatible declaration may therefore be
loaded into typed records, but it cannot be rendered or passed to calculator
execution.
