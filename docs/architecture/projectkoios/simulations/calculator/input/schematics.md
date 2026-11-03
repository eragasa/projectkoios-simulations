# Prepared calculator-input schematics

## Preparation flow

```mermaid
flowchart TD
    simulation[Exact SimulationRecord]
    translator[Outward QE, VASP, or other input translator]
    bytes[Rendered native input bytes]
    requirements[Exact external-file requirements]
    mappings[Charge and spin mapping observations]
    record[Neutral CalculatorInputRecord]

    simulation --> translator
    translator --> bytes --> record
    translator --> requirements --> record
    translator --> mappings --> record
```

The translator is outward; the returned immutable record is protected-core data.

## Content identity

```mermaid
flowchart TD
    record[CalculatorInputRecord]
    simulation[Simulation content reference]
    integration[Integration identity]
    representation[Input representation and schema]
    artifacts[Ordered artifacts: role, basename, bytes, size, SHA-256]
    requirements[Ordered external requirements and exact file identities]
    mappings[Mapping observations]
    provenance[Preparation provenance]

    simulation --> record
    integration --> record
    representation --> record
    artifacts --> record
    requirements --> record
    mappings --> record
    provenance --> record
```

Any changed file bytes, order, external identity, integration, or source
simulation creates a different complete record.

## Execution and evidence boundary

```mermaid
flowchart TD
    record[CalculatorInputRecord]
    executable[Calculator executable]
    authority[External authorization and deployment resolution]
    execution[Calculator execution]
    evidence[SimulationEvidenceRecord references CalculatorInputRecord]

    record --x executable
    record --> authority --> execution --> evidence
```

The crossed edge means a prepared record alone cannot start a calculator.

## Dependency direction

```mermaid
flowchart LR
    workflows[simulations.workflows]
    integrations[integrations]
    evidence[simulations.evidence]
    input[simulations.calculator.input]
    runtime[Live runtime or local deployment paths]

    workflows --> input
    integrations --> input
    evidence --> input
    input --x integrations
    input --x workflows
    input --x runtime
```

## Existing API migration

```mermaid
flowchart LR
    current[Current PwDft input projection]
    text[Rendered text and unresolved basenames]
    future[Atomic PwDft input-rendering result]
    record[CalculatorInputRecord with exact bytes and external identities]

    current --> text
    current --> future --> record
    text --x record
```

There is no period in which evidence may ambiguously reference either form.
