# QE SCF calculator-input translation

`QE_SCF_INTEGRATION_ID` is the stable registry identity. `QeScfInputProjector`
translates a calculator-neutral `PwDftScfRequest` plus an exact
`StructureResolution` into deterministic `pw.x` input. The existing Python name
uses “projection”; architecturally this is calculator-input translation.

The neutral specification stores its scientific electronic convergence
threshold in eV. QE configuration stores the native `electronic_tolerance_ry`
and a separate `electronic_atol_ry`. The latter is only the absolute tolerance
for qualifying the eV-to-Ry mapping. It is not rendered as `conv_thr`, is not a
scientific convergence threshold, and is not an acceptance policy.

## Documents

- [Implementation](implementation.md)
- [Schematics](schematics.md)
- [Numeric contract](numeric.md)
- [Scientific semantics](scientific.md)
- [`QeScfInputProjector`](QeScfInputProjector/index.md)

## Defect extension status

The translator maps integral `delta_n_electrons` to QE `tot_charge`, derives
collinear `nspin`, emits a constrained `tot_magnetization`, maps a common
per-species scalar initial moment to `starting_magnetization(i)`, and checks bound
pseudopotential filenames. Different site moments for one QE species are
rejected because the native species-level field cannot represent them. It
returns the exact `CalculatorInputRecord`. Complete defect evidence additionally
requires normalization to:

- retain the implemented QE positive-charge convention and conversion in an
  exact mapping;
- render the selected collinear, noncollinear, or spin-orbit mode;
- retain spin initialization and any declared total-spin constraint as separate
  exact mappings;
- preserve exact pseudopotential identities for neutral electron-count meaning;
- reject a request whose neutral charge/spin intent cannot be represented
  exactly by the supported QE input model.

Neutral Si:P requires collinear spin polarization and doublet intent while
`delta_n_electrons == 0`. Enabling spin and constraining a spin-channel
difference are distinct native operations and must not be conflated.

The resulting input does not authorize `pw.x` execution.
