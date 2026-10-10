# Plane-wave DFT relaxation schematics

## Request and result flow

```text
PwDftRelaxationSpecification
  structure + charge + spin
  scope + cell-relaxation mode
  sampling + convergence controls
                |
                v
PwDftRelaxationRequest with evaluation identity
                |
                v
calculator-input translation -> CalculatorInputRecord
                |
                v
external authorized execution
                |
                v
provider-native retained artifacts
                |
                v
outward normalization adapter
                |
                v
PwDftRelaxationObservation -> PwDftRelaxationResult
```

## Fixed-cell observation

```text
starting exact lattice --------------------------+
                                                  +--> final UnitCell
provider-observed final atomic positions --------+
provider-reported lattice ----------------------------> consistency observation
```

The provider-reported lattice does not replace the starting lattice when the
cell was not an allowed degree of freedom.

## Variable-cell observation

```text
provider-observed final atomic positions ----+
provider-observed final lattice -------------+--> final UnitCell
final stress/pressure -----------------------> convergence observation
```

The exact cell-relaxation mode determines which lattice changes were allowed.

## Structure publication

```text
starting StructureResolution
PwDftRelaxationResult -> canonical observation bytes
SimulationEvidenceRecord -> matching normalization digest
                |
                v
PwDftRelaxedStructurePublisher
                |
                v
ObservedStructureProvenance + exact base-UnitCell bytes
```

A relaxation result does not mutate the structure library by itself.

## Dependency direction

```text
integrations ---------------------> dft.pw.relaxation
simulations.workflows -----------> dft.pw.relaxation
simulations.evidence ------------> dft.pw.relaxation records

dft.pw.relaxation -X-> integrations
protected relaxation -X-> workflows or live runtime
```
