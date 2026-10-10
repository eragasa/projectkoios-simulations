# Plane-wave DFT defect-formation workflow implementation rules

## Planned module map

```text
src/python/projectkoios/simulations/workflows/pw_dft_defect_formation/
  __init__.py
  composition.py
  policy.py
  workflow/
    __init__.py
    definition.py
```

- `composition.py` will bind exact study inputs and produce typed requirements,
  qualified derivations, and study observations.
- `policy.py` will define explicit size-convergence thresholds, stability
  requirements, budgets, and accept/extend/inconclusive decisions.
- `workflow/definition.py` will be added only if a reviewed engine-neutral shape
  is required. It must not claim to be executable topology without complete
  arcs, guards, token expressions, and occurrence semantics.

No source package or public symbol described here exists yet.

## Allowed imports

Production modules may import:

- the Python standard library;
- protected `projectkoios.simulations` structure, simulation-library, evidence,
  SCF, relaxation, method-neutral `simulations.defects`, and DFT-specific
  `simulations.dft.defects` contracts; and
- public sibling workflow contracts under
  `projectkoios.simulations.workflows`.

They must not import:

- `projectkoios.integrations` or `projectkoios.adapters`;
- pymatgen or mp-api;
- repository tools or examples;
- Applications or another downstream package; or
- a live generic Workflow service, scheduler, worker, persistence layer, or
  runtime implementation.

## Exact input roles

One study declaration identifies complete records for:

- the source conventional silicon cell;
- every pristine supercell specification;
- every ideal host-geometry Si:P and Si:B defect specification;
- every ion-only fixed-cell relaxation and resulting final-SCF specification;
- every full ion-and-cell relaxation and resulting final-SCF specification;
- diamond-silicon reference relaxation and SCF;
- hull-selected boron and phosphorus reference relaxation and SCF;
- calculator-specific input-rendering profiles; and
- evidence already available for any of those roles.

A friendly ID alone cannot satisfy a role. Cross-role validation must reject
mismatched sizes, defect deltas, impurity species, structures, incompatible
calculation models, spin treatments, or any violation of
`charge_state == -delta_n_electrons`. It must prove that the ideal defect has the
host lattice and positions, that ion-only relaxation preserves that lattice,
and that full relaxation descends from the same ion-relaxed defect under
explicit pressure controls. Every neutral Si:P role must declare collinear spin
polarization and one more electron in one spin channel than the other. Bulk,
Si:B, and nonneutral Si:P roles must each carry their own explicit spin
specification rather than inheriting the Si:P value.

## Decisions and handoffs

Composition produces immutable decisions such as:

```text
EvidenceAvailable
RelaxationRequired
FinalScfRequired
CompatibilityRejected
FormationEnergyDerived
RelaxationEnergiesDerived
AdditionalSizeRequired
SizeConvergenceAccepted
SizeConvergenceInconclusive
BudgetExhausted
```

Names are provisional until implementation review. None of these decisions
starts a calculator. A required calculation becomes a neutral request or
external execution handoff whose authorization is owned elsewhere.

## Acceptance policy

The policy must state:

- which ordered sizes participate;
- whether it assesses formation energy, ionic relaxation energy, cell-strain
  relaxation energy, or total relaxation energy;
- the energy-difference metric, sign convention, and units;
- the numerical threshold;
- the required stable window;
- handling of missing or rejected evidence;
- maximum extension or calculation budget; and
- whether the outcome is accepted, rejected, inconclusive, or budget-exhausted.

Mechanical compatibility qualification is an input to acceptance; it is not
itself acceptance.

## Provider composition

Repository tools may resolve integration IDs to QE or VASP input renderers and
output parsers and may create exact `CalculatorInputRecord` values. Production
workflow code sees only neutral identities, specifications, handoffs, exact
prepared-input records, and normalized evidence. It cannot read
`local-execution.toml` or infer authority from installed executables.

## Required verification

Tests must cover the full 64/216/512 role matrix, missing roles, exact-record
ambiguity, impurity and size mismatch, charge/electron-count sign and mismatch
validation, neutral-only formation-energy enforcement, required neutral-Si:P
spin polarization, spin mismatch rejection, evidence qualification failure,
chemical-potential provenance, formation-energy sign
convention, threshold boundaries, stable windows, budgets, and deterministic
decision ordering. Repository gates must enforce provider-independent imports
and calculator-free tests.
