# Calculator-neutral defect energetics schematics

## Structural and energetic boundaries

```text
bulk UnitCell + UnitCellDefectDelta
                 |
                 v
          ideal defect UnitCell
                 |
                 +---------------------- structure domain
                 |
          explicit simulations
                 |
          qualified evidence
                 |
                 +---------------------- defect energetics domain
                 v
          formation-energy result
```

Applying a delta does not imply relaxation, an energy, or scientific validity.

## Neutral substitution energy

```text
local defect evidence ------------------ E_defect -----+
local pristine evidence ---------------- E_pristine ---+
local host reference evidence ---------- mu_Si --------+--> pure derivation
local impurity reference evidence ------ mu_X ---------+          |
explicit atom-count delta ------------------------------+          v
                                                     E_formation
```

For `Si_(N-1)X`, the result is:

```text
E_defect - E_pristine + mu_Si - mu_X
```

Materials Project energies are absent from this graph.

## Elemental phase selection boundary

```text
Materials Project entries
          |
          v
pymatgen one-element hull
          |
          v
selected phase identity and structure
          |
          v
compatible local relaxation + final energy evaluation
          |
          v
local chemical-potential evidence
```

The hull selection is database-, compatibility-scheme-, and zero-temperature-
qualified. It is not an experimental standard-state or finite-temperature
claim.

## Relaxation and strain-energy flow

```text
ideal host-geometry defect
  host lattice + host positions
            |
            +--> final energy ----------------------- E_ideal
            |
            v
ion-only relaxation, fixed host lattice
            |
            +--> final energy ----------------------- E_ion_only
            |
            v
full ion-and-cell relaxation at declared pressure
            |
            +--> final energy ----------------------- E_fully_relaxed

E_ideal - E_ion_only          = ionic relaxation energy
E_ion_only - E_fully_relaxed = stored cell-strain relaxation energy
E_ideal - E_fully_relaxed    = total relaxation energy
```

The first zero-pressure implementation compares qualified final single-point
energies. The plane-wave DFT workflow supplies final-SCF energies. Another
method may supply a different exact final-energy observation. Nonzero-pressure
comparison requires a separately declared common enthalpy contract.

## Size-convergence flow

```text
64-atom formation/strain energy ----+
216-atom formation/strain energy ---+--> ordered mechanical differences
512-atom formation/strain energy ---+                  |
                                                       v
                                         workflow-owned acceptance policy
```

## Dependency direction

```text
simulations.workflows.pw_dft_defect_formation
                         |
                         v
simulations.defects ---> simulations.evidence
          |                    |
          +--------------------+--> simulations.library and structure

simulations.defects -X-> method-specific integrations
simulations.defects -X-> simulations.workflows
simulations.defects -X-> pymatgen or mp-api
```
