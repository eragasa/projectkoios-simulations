# Plane-wave DFT SCF workflow

Petri-net name inventory and engine-hiding façade with explicit start and
terminal places. The executable topology remains in `pw_dft_scf.cpn.net`.

## Ownership boundary

This package boundary mirrors `src/python/projectkoios/simulations/workflows/pw_dft_scf/workflow/__init__.py` in `projectkoios.simulations.workflows.pw_dft_scf.workflow`. It owns domain composition only: it neither selects or executes a calculator provider nor owns generic Workflow lifecycle state. The historical sibling import path is intentionally unavailable.
