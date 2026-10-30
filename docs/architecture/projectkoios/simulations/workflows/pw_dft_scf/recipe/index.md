# Plane-wave DFT SCF recipes

`PwDftScfRecipe`, `PwDftScfSingleCalculationRecipe`,
`PwDftScfKpointConvergenceRecipe`, `PwDftScfCutoffConvergenceRecipe`, and
`PwDftScfGridConvergenceRecipe` cover the four currently implemented scientific
modes.

The convergence recipes vary a cubic mesh-density integer and/or wavefunction
cutoff. `PwDftScfGridConvergenceRecipe` is reused unchanged by
[`pw_dft_bulk_qualification`](../../pw_dft_bulk_qualification/index.md). The
additive typed correlation binds every generated coordinate to an exact neutral
cutoff realization, projected request/input, occurrence, evidence bytes, and
adapter mapping before selecting the full k-point policy. QE-native cutoff
controls remain outward evidence. Noncubic recipes and independently varying
the density/potential cutoff are not required by the first route.
