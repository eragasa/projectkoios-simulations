# Plane-wave DFT SCF configuration

`PwDftScfRuntimeConfiguration` bounds internal progress. `PwDftScfCampaignConfiguration` binds a scientific recipe to a registered calculator integration.

## Ownership boundary

This package boundary mirrors `src/python/projectkoios/simulations/workflows/pw_dft_scf/configuration.py` in `projectkoios.simulations.workflows.pw_dft_scf.configuration`. It owns domain composition only: it neither selects or executes a calculator provider nor owns generic Workflow lifecycle state. The historical sibling import path is intentionally unavailable.
