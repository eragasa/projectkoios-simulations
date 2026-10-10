# Simulation library schematics

## Identity layers

```text
stable simulation_id
        |
        | may name several historical records
        v
SimulationRecord
  representation + schema version + byte size + SHA-256 + provenance
        |
        v
verified specification bytes
        |
        v
PwDftScfSpecification or PwDftRelaxationSpecification
```

Stable lookup is convenient; the complete record is authoritative.

## Scientific dependency graph

```text
exact StructureRecord ------------------+
                                         |
exact pseudopotential requirements ------+--> PwDftSimulation
                                                   |
                           +-----------------------+---------------------+
                           |                                             |
                           v                                             v
                PwDftScfSpecification                     PwDftRelaxationSpecification
                  + SCF sampling                          + scope/sampling/convergence
```

No dependency edge points to a provider integration or local filesystem path.

## Specification and occurrence separation

```text
SimulationLibrary
      |
      v
resolved immutable specification
      |
      +--> workflow recipe derives scientific coordinates
      |
      v
request with evaluation_id
      |
      v
workflow occurrence
      |
      v
calculator-specific input rendering and separately authorized execution
```

A retry creates another attempt for the same occurrence. A new convergence
coordinate creates a new occurrence. Neither changes the identity of a stored
base specification unless a derived specification is explicitly published.

## Dependency direction

```text
simulations.workflows ---------> simulations.library
integrations ------------------> simulations.library
repository tools --------------> simulations.library

simulations.library -X-> simulations.workflows
simulations.library -X-> integrations
simulations.library -X-> Applications or live Workflow runtime
```

## Data placement

```text
production contracts:  src/python/projectkoios/simulations/library
reviewed examples:     examples/libraries/simulations
workflow studies:      examples/workflows
provider profiles:     examples/integrations
machine deployment:    ignored local-execution.toml or injected paths
```

The production package defines resolution behavior. It does not embed one
operator's catalog or deployment paths.
