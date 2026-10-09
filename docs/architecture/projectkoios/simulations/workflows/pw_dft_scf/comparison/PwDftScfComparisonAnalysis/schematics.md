# PwDftScfComparisonAnalysis schematics

## Contract flow

- `request` preserves the exact comparison inputs. - `interpretation` bounds the scientific claim. - `native_left_minus_right_mev_per_atom` preserves the native difference. - `aligned_left_minus_right_mev_per_atom` records the declared aligned difference. - `irreducible_kpoint_counts_match` reports comparable observed counts when present. - `wavefunction_cutoff_left_minus_right_ev` reports the observed cutoff difference when present. - `qualifications` records mandatory and reference-specific limitations.

```text
caller --> PwDftScfComparisonAnalysis --> typed domain value or decision
             |
             +--> protected projectkoios.simulations core contracts
```

## Documented children

No child documentation nodes; the index defines the complete local role.

## Dependency and authority boundary

`projectkoios.simulations.workflows.pw_dft_scf.comparison` points inward only to the protected simulation core or to other owner workflow modules. It does not select a calculator provider, import `projectkoios.integrations`, discover an executable, grant execution authority, or own generic Workflow compiler/runtime state. Domain topology or guards described here remain owner source declarations; canonical CPN places, transitions, and plans remain compiler-owned.
