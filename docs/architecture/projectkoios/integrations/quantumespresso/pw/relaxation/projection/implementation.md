# QE relaxation calculator-input translation implementation

## Boundary and inputs

The common `project_relaxation_input` implementation is outward provider code.
It consumes:

1. `PwDftRelaxationRequest`, whose specification owns scientific intent;
2. a matching `StructureResolution` with verified exact starting geometry;
3. `QeRelaxationInputConfiguration`, whose fields are provider-native policy;
4. the explicit QE calculation mode; and
5. optional lattice-vector controls required only for `vc-relax`.

It creates `ResolvedPwDftSimulation` before provider translation so exact
structure, composition, charge, spin, and pseudopotential relationships are
validated at the resolved boundary.

## Validation and rendering

Translation rejects mismatched species, non-UPF pseudopotentials, mismatched
pseudopotential filenames, unsupported spin and site moments, and non-fixed
occupation. Disabled spatial and time-reversal reductions map independently to
QE `nosym` and `noinv`; enabled values retain QE's documented false defaults.
Translation then converts the neutral scientific electronic threshold from eV
to Ry and requires agreement with `electronic_tolerance_ry` within
`electronic_atol_ry`.

After qualification, only `electronic_tolerance_ry` is written to the
`&ELECTRONS` card as `conv_thr`. `electronic_atol_ry` remains provider mapping
configuration and is not calculator input.

The implementation independently converts wavefunction cutoff, ionic energy
tolerance, and force tolerance. Variable-cell adapters additionally map the
selected neutral cell mode to explicit QE cell degrees of freedom; unsupported
modes raise instead of falling back to QE defaults.

## Retained calculation declarations

`QeRelaxationCalculationTomlLoader` requires both numeric fields in the closed
`[sampling]` mapping. `QeRelaxationCalculationRenderer` constructs the neutral
specification from the retained native declaration, propagates
`electronic_atol_ry` into the fixed- or variable-cell projection configuration,
and renders through the same translation path. Unknown or missing declaration
keys are rejected.

The result remains a pure prepared-input transformation. Filesystem writing,
calculator execution, normalization, evidence, and acceptance are separate
operations.
