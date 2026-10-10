# Simulation evidence schematics

## Record correlation

```text
SimulationRecord ---------------------+
                                      |
CalculatorInputRecord ----------------+--> completed evaluation
                                      |          |
occurrence / attempt correlation ------+          v
                                      |   mechanical execution evidence
native artifact identities ------------+          |
                                                 v
                                      normalized scientific observation
                                                 |
                                                 v
                                      SimulationEvidenceRecord
```

Every edge records identity or provenance. None grants authority to repeat the
execution.

## Specification, evidence, and analysis

```text
SimulationLibrary        Evidence library             Derived analysis
-----------------        ----------------             ----------------
what should be done ---> what was observed ---------> what is calculated
scientific intent        artifacts and facts          from qualified evidence
```

Calculated energy belongs to evidence. Formation energy belongs to derived
analysis. Scientific acceptance belongs to workflow policy.

## Defect-structure publication stages

```text
exact host supercell + defect delta
          |
          v
ideal host-geometry defect StructureRecord
  same host lattice and positions; changed species only
          |
          v
ATOMIC_POSITIONS relaxation evidence
          |
          v
ion-relaxed StructureRecord
  same host lattice; relaxed positions
          |
          v
ATOMIC_POSITIONS_AND_CELL relaxation evidence
          |
          v
fully relaxed StructureRecord
  relaxed positions and lattice
```

Each arrow is an explicit derivation or evidence-backed publication. There is
no edge directly from an ideal defect delta to either relaxed structure.

## Authority boundary

```text
external authorized runtime ---> provider execution ---> evidence construction

SimulationEvidenceRecord -X-> calculator executable
SimulationEvidenceRecord -X-> retry or resubmission
SimulationEvidenceRecord -X-> scientific acceptance
```

## Import direction

```text
integrations --------------------> simulations.evidence
simulations.workflows -----------> simulations.evidence
simulations.defects -------------> simulations.evidence

simulations.evidence -X-> integrations
simulations.evidence -X-> simulations.workflows
simulations.evidence -X-> live Workflow runtime
```
