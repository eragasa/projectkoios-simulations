# Plane-wave DFT SCF integration

`PwDftScfIntegration.project()` returns the protected-core
`CalculatorInputRecord` containing exact prepared artifacts, external
requirements, source correlation, and mapping observations.
`PwDftScfIntegration` is the simulation-owned abstract integration contract; it
does not depend on a behaviorless cross-domain adapter marker.
`PwDftScfIntegrationRegistry` resolves installed instances.
