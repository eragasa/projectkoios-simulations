# Plane-wave DFT SCF integration

`PwDftScfRenderedInput` and `PwDftScfInputProjection` describe native inputs.
`PwDftScfIntegration` is the simulation-owned abstract integration contract;
it does not depend on a behaviorless cross-domain adapter marker.
`PwDftScfIntegrationRegistry` resolves installed instances.
