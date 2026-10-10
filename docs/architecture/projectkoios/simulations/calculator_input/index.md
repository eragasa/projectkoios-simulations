# Exact prepared calculator inputs

## Status

An initial protected-core implementation now provides exact artifacts, exact
external requirements, neutral-to-native mappings, source references, and the
content-addressed `CalculatorInputRecord`. Existing QE/VASP SCF and relaxation
renderers still require atomic migration from their older rendered-input return
shapes before every calculator input is emitted through this record.

## Purpose

A `CalculatorInputRecord` answers:

```text
Which exact calculator input files and required external files were prepared
from which exact simulation specification for which integration?
```

It is immutable pre-execution evidence. It does not authorize execution, prove
that required files are installed, or record a result.

## Record contents

The record contains:

- complete `SimulationRecord` identity through an acyclic content reference;
- `CalculatorIntegrationId`;
- calculator-input representation and schema version;
- ordered rendered `CalculatorInputArtifact` records;
- ordered exact `CalculatorExternalInputRequirement` records;
- explicit mapping observations for neutral charge and spin intent;
- byte size and SHA-256 for each rendered artifact;
- deterministic aggregate identity; and
- immutable preparation provenance.

A rendered artifact carries a logical basename, role, media type, byte size,
SHA-256, and bytes or an exact storage reference. An external requirement carries
its scientific role and complete pseudopotential or other required-file
identity, never only a local basename.

## Input translation

QE, VASP, and other integrations translate neutral scientific specifications
into native input files. Existing Python APIs call this operation “projection”;
the architecture documentation uses the plainer terms “calculator-input
translation” and “input rendering.”

The outward integration creates the native files and returns a neutral
`CalculatorInputRecord`. The protected record contains no QE namelist object,
VASP INCAR model, executable path, scratch directory, or credential.

## Charge and spin

The record preserves both neutral intent and the exact native values rendered.
For example, a translator must record how `delta_n_electrons` became a native
total-charge or electron-count setting and how spin-polarized doublet intent
became native spin-channel and initialization fields.

A signed value is never copied merely because two fields share the word
“charge.” Mapping is explicit and tested for each integration.

## Relationship to evidence

```text
SimulationRecord -> CalculatorInputRecord -> authorized execution
                                             |
                                             v
                                  SimulationEvidenceRecord
```

Evidence references the complete prepared-input identity. A rerendered input
with changed bytes is a different record even when the stable simulation ID is
unchanged.

## Non-goals

This package does not choose a calculator, discover executables, resolve local
paths, authorize a run, parse outputs, manage retries, or decide scientific
acceptance.

See [`implementation.md`](implementation.md) for the planned schema and
migration and [`schematics.md`](schematics.md) for preparation and authority
flows.
