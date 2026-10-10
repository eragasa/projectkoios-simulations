# QE SCF calculator-input translation

`QE_SCF_INTEGRATION_ID` is the stable registry identity. `QeScfInputProjector`
renders common requests through the maintained QE assembler. The existing
Python name uses “projection”; architecturally this is translation into exact QE
input files.

## Defect extension status

The current translator maps integral `delta_n_electrons` to QE `tot_charge`,
derives collinear `nspin`, emits a constrained `tot_magnetization`, rejects
unsupported site-resolved initial moments, and checks bound pseudopotential
filenames. It does not yet create the required exact prepared-input record.
Before complete defect evidence, translation must:

- retain the implemented QE positive-charge convention and conversion in an
  exact mapping;
- render the selected collinear, noncollinear, or spin-orbit mode;
- render spin initialization and any declared total-spin constraint separately;
- preserve exact pseudopotential identities for neutral electron-count meaning;
- return a neutral `CalculatorInputRecord` containing the rendered bytes and
  mapping observations; and
- reject a request whose neutral charge/spin intent cannot be represented
  exactly by the supported QE input model.

Neutral Si:P requires collinear spin polarization and doublet intent while
`delta_n_electrons == 0`. Enabling spin and constraining a spin-channel
difference are distinct native operations and must not be conflated.

The resulting record does not authorize `pw.x` execution.
