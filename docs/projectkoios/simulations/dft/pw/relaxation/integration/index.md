# `projectkoios.simulations.dft.pw.relaxation.integration`

Defines the simulation-owned abstract input-integration contract, fail-closed
registry, and generic selection wrapper. Integrations return the shared exact
`CalculatorInputRecord`; no relaxation-specific rendered-input or projection
record remains.

## Public symbols

- `PwDftRelaxationIntegration`
- `PwDftRelaxationIntegrationRegistry`
- `PwDftRelaxationInputWrapper`
