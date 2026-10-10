# Generic unit-cell defect deltas

## One model for bulk-cell changes

`UnitCellDefectDelta` is the single calculator-neutral declaration for an ideal
vacancy, interstitial, substitution, or multi-site defect complex. It contains:

```text
bulk_cell: UnitCell
removals: tuple[int, ...]
additions: tuple[Atom, ...]
charge_state: int = 0
```

Removal indices address the original `bulk_cell.atomic_basis.atoms` tuple.
They must be unique and strictly increasing. All removals are interpreted
simultaneously; indices never shift while the delta is applied. Retained bulk
atoms preserve their original relative order, and additions follow in declared
order.

A vacancy has removals only. An interstitial has additions only. A substitution
removes one or more sites and adds replacement atoms. A complex uses any valid
combination. Separate vacancy, interstitial, and substitution class hierarchies
are intentionally absent.

## Validation and application

A delta must make at least one change and leave at least one atom. Addition
coordinates must be finite fractional coordinates in `[0, 1)`. After removals,
an addition may not collide exactly with a retained position, and addition
positions must be unique. `charge_state` is a built-in integer.

`UnitCellDefectDeltaApplicator.action()` returns a correlated
`UnitCellDefectDeltaResult`. The result contains an exact base `UnitCell`, not a
`PrimitiveUnitCell`, `ConventionalUnitCell`, or pristine `SuperCell`. The
applicator preserves the bulk lattice and lattice parameter, applies all
original-index removals, and appends additions. The result validates those
mechanical invariants.

`charge_state` describes the defect configuration in units of positive
fundamental charge: a positive value means electrons have been removed. It is
not encoded in the atomic structure bytes, does not add a compensating
background, and does not itself select an electronic-state treatment.

A calculation that realizes the declared charge records
`PwDftSimulation.delta_n_electrons`, defined relative to the neutral electron
count for the same nuclei and exact pseudopotentials. Positive
`delta_n_electrons` means electrons are added. The required invariant is:

```text
charge_state == -delta_n_electrons
```

Thus a `+1` defect calculation has `delta_n_electrons == -1`. A neutral defect
has both values equal to zero. The structural declaration remains the authority
for the intended defect charge; the simulation field records how that charge is
realized electronically and must match it.

## Concrete ideal silicon declarations

[`silicon_substitutional_defects.py`](../../../../../../examples/workflows/pw_dft_scf/structures/silicon_substitutional_defects.py)
contains concrete neutral, unrelaxed Si:P and Si:B declarations:

1. resolve exact `Si.ConventionalUnitCell` from the reviewed manifest;
2. construct a diagonal `(2, 2, 2)` pristine `SuperCell`, yielding 64 Si atoms;
3. select original supercell atom index `0`, whose
   `UnitCellSiteOrigin` is source atom `0` at translation `(0, 0, 0)`;
4. remove index `0` and add P or B at that exact fractional position;
5. set `charge_state=0` and apply the delta.

`Si:P`, `Si:B`, and Kröger–Vink notation are human-readable labels, not
canonical machine identities. The exact declaration identity is the complete
combination of the parent `StructureRecord`, `(2, 2, 2)` transformation,
original removal index, ordered added atom and position, and charge state. No
standalone `StructureRecord` identifier is assigned to either derived result,
because the version-one library codec stores primitive and conventional source
cells only. Persisting derived base `UnitCell` values requires a separately
reviewed schema and provenance contract.

The example fixes one ideal declaration; it does not assert that the selected
size, site, charge state, spin state, or geometry is scientifically appropriate
for a calculation.

## Elemental reference selection

Absolute neutral substitutional formation energies additionally require
explicit Si, P, and B chemical potentials. The outward
[`projectkoios.integrations.materials_project`](../../../integrations/materials_project/index.md)
integration selects P and B reference entries from separately declared
single-element pymatgen convex hulls. The selected Materials Project IDs,
thermodynamic compatibility scheme, energies per atom, entry counts, and source
structures must be retained. The hull result is a database-qualified reference
choice, not a universal finite-temperature ground-state claim.

Chemical-potential terms cancel when comparing matched formation energies across
supercell sizes, but retaining the elemental references makes the same evidence
set usable for absolute formation energies.

A relaxed defect structure is a distinct observation requiring calculation and
evidence provenance. It must never be inferred merely by applying an ideal
delta.

The defect API does not authorize calculator execution.
