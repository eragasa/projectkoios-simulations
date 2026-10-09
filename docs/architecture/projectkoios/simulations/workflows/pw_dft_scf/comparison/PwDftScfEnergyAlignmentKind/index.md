# PwDftScfEnergyAlignmentKind

- `NATIVE` preserves the calculator-native energy zero.
- `EXPLICIT_REFERENCE` subtracts an explicitly identified reference.

## Ownership boundary

This public `PwDftScfEnergyAlignmentKind` contract mirrors `src/python/projectkoios/simulations/workflows/pw_dft_scf/comparison.py` in `projectkoios.simulations.workflows.pw_dft_scf.comparison`. It owns domain composition only: it neither selects or executes a calculator provider nor owns generic Workflow lifecycle state. The historical sibling import path is intentionally unavailable.
