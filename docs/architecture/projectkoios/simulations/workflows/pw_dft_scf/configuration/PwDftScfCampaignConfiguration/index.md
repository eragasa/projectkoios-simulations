# PwDftScfCampaignConfiguration

Fields: `integration_id`, `recipe`, `runtime`.

## Ownership boundary

This public `PwDftScfCampaignConfiguration` contract mirrors `src/python/projectkoios/simulations/workflows/pw_dft_scf/configuration.py` in `projectkoios.simulations.workflows.pw_dft_scf.configuration`. It owns domain composition only: it neither selects or executes a calculator provider nor owns generic Workflow lifecycle state. The historical sibling import path is intentionally unavailable.
