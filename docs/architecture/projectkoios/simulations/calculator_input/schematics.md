# Prepared calculator-input schematics

## Preparation flow

```text
exact SimulationRecord
        |
        v
outward QE / VASP / other input translator
        |
        +--> rendered native input bytes
        +--> exact external-file requirements
        +--> charge and spin mapping observations
        |
        v
neutral CalculatorInputRecord
```

The translator is outward; the returned immutable record is protected-core data.

## Content identity

```text
CalculatorInputRecord
  simulation content reference
  integration identity
  input representation + schema
  ordered rendered artifacts {role, basename, bytes, size, SHA-256}
  ordered external requirements {role, exact file identity}
  mapping observations
  preparation provenance
```

Any changed file bytes, order, external identity, integration, or source
simulation creates a different complete record.

## Execution and evidence boundary

```text
CalculatorInputRecord
        |
        +----------------X----------------> calculator executable
        |
        v
external authorization and deployment resolution
        |
        v
calculator execution
        |
        v
SimulationEvidenceRecord references CalculatorInputRecord
```

The crossed edge means a prepared record alone cannot start a calculator.

## Dependency direction

```text
simulations.workflows -----------> simulations.calculator_input
integrations --------------------> simulations.calculator_input
simulations.evidence ------------> simulations.calculator_input

simulations.calculator_input -X-> integrations
simulations.calculator_input -X-> workflows
simulations.calculator_input -X-> live runtime or local deployment paths
```

## Existing API migration

```text
current
PwDft*InputProjection
  rendered text + unresolved basenames

future atomic contract
PwDft* input rendering result
  CalculatorInputRecord with exact bytes and external identities
```

There is no period in which evidence may ambiguously reference either form.
