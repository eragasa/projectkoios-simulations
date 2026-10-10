# Plane-wave DFT defect binding schematics

## Two-layer ownership

```text
projectkoios.simulations.dft.defects
  exact PwDft specifications
  electron count, spin, pseudopotentials, XC, cutoffs, k points
  final-SCF evidence and prepared calculator inputs
                     |
                     v
       DFT compatibility qualification
                     |
                     v
projectkoios.simulations.defects
  chemical-potential terms
  formation-energy arithmetic
  relaxation/strain-energy arithmetic
  mechanical size differences
```

The upper layer establishes that the DFT energies are eligible inputs. The lower
layer owns equations that are not specific to DFT.

## Charge binding

```text
UnitCellDefectDelta.charge_state -----+
                                      +--> require q = -delta_n_electrons
PwDftSimulation.delta_n_electrons ----+
                                      |
                                      v
                         DFT defect binding record
```

Changing Si to P or B changes the neutral valence count through the species and
pseudopotentials. It does not by itself change `delta_n_electrons`.

## Neutral Si:P spin binding

```text
neutral Si:P structure
        |
        +--> delta_n_electrons = 0
        +--> collinear spin polarized
        +--> one-electron spin-channel difference
        `--> doublet study intent
                    |
                    v
ideal / ion-only / fully relaxed / final-SCF records
                    |
                    v
require compatible spin treatment before energy subtraction
```

## Provider boundary

```text
QE or VASP integration
  renders exact input and parses native output
                    |
                    v
neutral CalculatorInputRecord + normalized DFT observation
                    |
                    v
projectkoios.simulations.dft.defects
                    |
                    v
method-neutral qualified energy terms
```

The protected DFT package does not import QE or VASP. It sees neutral records
created by those outward integrations.

## Dependency direction

```text
simulations.workflows.pw_dft_defect_formation
                         |
                         v
simulations.dft.defects ---> simulations.defects
          |                        |
          +------------------------+--> evidence, library, structure

simulations.defects -X-> simulations.dft.defects
simulations.dft.defects -X-> workflows or integrations
```
