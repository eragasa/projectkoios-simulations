# Plane-wave DFT defect-formation workflow schematics

## Study composition

```text
exact structure records
        |
exact simulation records
        |
exact prepared calculator-input records
        |
        v
resolve declared study roles
        |
        +--> ideal + <100> + <111> defect starts
        |          |
        |          v
        +--> ion-only relaxation: fixed host lattice, reductions disabled
        |          |
        |          +--> publish structures --> final SCFs
        |          `--> select lowest compatible observed basin
        |          v
        +--> optional full ion-and-cell diagnostic: declared pressure
        |
        +--> each missing calculation becomes a non-authorizing handoff
        |
        v
qualify completed evidence
        |
        +--> local Si/B/P chemical potentials
        +--> pristine and Si:P/Si:B formation energies
        `--> ionic relaxation and residual-stress observations
        |
        v
ordered 64 / 216 / 512 atom observations
        |
        v
workflow-owned size-convergence policy
        |
        +--> accepted
        +--> additional size required
        +--> inconclusive or rejected
        `--> budget exhausted
```

No handoff authorizes calculator execution.

## Reuse boundary

```text
pw_dft_defect_formation
      |
      +--> pw_dft_relaxation public composition
      +--> pw_dft_scf public recipes/results
      +--> simulations.dft.defects DFT compatibility binding
      +--> simulations.defects method-neutral derivations
      +--> SimulationLibrary and evidence records
      `--> structure records and defect deltas

pw_dft_defect_formation -X-> QE/VASP integrations
```

Outward repository tools or applications bind neutral integration IDs to
provider implementations.

## Matched size series

```text
Si pristine 64  ----+     Si:P 64  ----+     Si:B 64  ----+
Si pristine 216 ----+-->  Si:P 216 ----+-->  Si:B 216 ----+--> assessments
Si pristine 512 ----+     Si:P 512 ----+     Si:B 512 ----+
        |                    |                  |
        +--------------------+------------------+
                             |
                  common local Si/B/P references
```

Each defect energy is paired with the pristine cell of the same declared
supercell transformation. Each size retains all three fixed-host defect starts,
relaxed structures, final SCFs, basin selection, and residual stress. Optional
full-cell release evidence is labeled as a finite-concentration diagnostic.
Elemental references are shared only after exact compatibility qualification.

## Runtime boundary

```text
scientific workflow decision
          |
          v
neutral request or execution handoff
          |
          v
external generic Workflow / provider binding
  occurrence identity, queues, leases, retries, cancellation, authority
          |
          v
normalized immutable evidence returned to composition
```

The production owner workflow contains none of the lifecycle mechanisms shown
inside the external binding.

## Future topology rule

```text
composition and policy records  !=  executable Petri-net topology
name inventory                  !=  arcs, guards, or token expressions
```

If an executable topology is later introduced, exactly one reviewed source must
be authoritative until a separately reviewed WORKFLOWS extraction replaces it.
