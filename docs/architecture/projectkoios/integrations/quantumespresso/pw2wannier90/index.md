# `integrations.quantumespresso.pw2wannier90`

## Ownership

Quantum ESPRESSO `pw2wannier90.x` native configuration and integration effects.
The package remains separate from calculator-neutral Wannier workflow policy.
It must not import `projectkoios.simulations.workflows`, select scientific
windows or projections, or grant execution authority.

## Artifact-route status

The implemented converter path projects and optionally executes an AMN/MMN/EIG
interface while configured UNK and SPN production remains unsupported. The
[artifact closure architecture](artifacts/index.md) records the planned split
between ordinary AMN/MMN localization and an explicitly supported optional
UNK-producing route. It does not claim that the route split or UNK production
is implemented.

Existing native subcomponents remain documented under configuration,
projection, execution, streams, and artifacts. A separately reviewed outward
adapter may map authenticated provider observations to neutral roles without
making this integration import the neutral workflow package.
