# Plane-wave DFT relaxation schematics

## Request and result flow

```text
PwDftRelaxationSpecification
  structure + charge + spin
  scope + explicit cell-relaxation mode
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

A relaxation result does not mutate the structure library by itself. Publication
proves exact mechanical correlation; it does not apply a workflow-owned
zero-pressure acceptance policy.

## Planned bulk qualification use

```text
provisional numerical qualification Q0@S0
  -> exact relaxation specification using S0 and Q0
  -> normalized protected relaxation result
  -> workflow-owned force/pressure/cell assessment
  -> exact published structure S1
  -> fresh SCF setting confirmation Q1@S1
```

If `Q1` changes the selected setting, workflow composition requests a new
relaxation and confirmation. The protected result remains immutable and does not
schedule or authorize that successor.

The protected specification remains unchanged. The bulk composition references
a neutral wavefunction and density/potential cutoff realization, and adapter
evidence proves the exact provider input realizes it; no provider keyword or QE
ratio enters this protected schema or the neutral terminal handoff.

## Dependency direction

```text
integrations / outward adapters --> dft.pw.relaxation
simulations.workflows -----------> dft.pw.relaxation
simulations.evidence ------------> dft.pw.relaxation records

dft.pw.relaxation -X-> integrations
protected relaxation -X-> workflows, adapters, tools, or live runtime
```
