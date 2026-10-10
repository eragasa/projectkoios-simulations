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

## Existing prerequisites

The target package composes rather than replaces the following implemented
capabilities:

- exact structure, pseudopotential, simulation-library, and calculator-input
  records;
- QE SCF projection, one-simulation execution, output normalization, and the
  authoritative single-SCF CPN lifecycle;
- calculator-neutral SCF recipes and energy-only convergence assessment;
- QE fixed-cell and variable-cell relaxation projection, execution, parsing,
  stress normalization, and result contracts;
- immutable simulation-evidence record types and pure relaxed-structure
  publication;
- exact supercell construction and ideal substitution deltas;
- charge, spin, symmetry, compatibility, formation-energy, relaxation-energy,
  and pairwise size-difference contracts; and
- exact starting relaxation specifications for Si, B `mp-160`, and P
  `mp-568348`.

These units are not yet a production chain. In particular, no production
assembler creates a `SimulationEvidenceRecord` from one execution, the
relaxation workflow stops at a non-authorizing projection handoff, and the
planned defect workflow package is absent.

## Remaining workflow and task inventory

Implementation proceeds in dependency order:

1. add byte-preserving live stdout emission to the single-simulation executor
   while retaining exact stdout and terminal failure evidence;
2. add a production evidence assembler that correlates one exact specification,
   prepared input, execution record, native artifacts, and normalized
   observation;
3. generalize convergence coordinates beyond cubic `(n, n, n)` meshes and add
   force and stress observations and numerical criteria alongside energy;
4. separate "numerical criterion satisfied" from scientific acceptance, then
   compose a parent convergence workflow from single-SCF child occurrences;
5. complete the relaxation action/event lifecycle from projection through
   external execution, normalization, evidence, and terminal outcome;
6. compose elemental-reference convergence, relaxation, final-SCF, evidence,
   relaxed-structure publication, and chemical-potential derivation for Si, B,
   and P;
7. regenerate pristine 64-, 216-, and 512-atom cells from the observed relaxed
   Si host and materialize ideal, `<100>`, and `<111>` starts;
8. compose qualified pre-relaxation, production relaxation, and final-SCF child
   occurrences for every dopant, size, and start;
9. select the lowest compatible converged observed basin while retaining every
   declared start and failure;
10. run matched pristine final SCFs and assemble defect/pristine compatibility;
11. derive formation energies and independently assess formation-energy and
    residual-stress size stability; and
12. optionally compose full-cell finite-concentration strain diagnostics.

Every numbered calculation task is one simulation occurrence. An external
Workflow runtime may sequence them with deployment concurrency one, but no
campaign object or executor may batch them into one calculator invocation.

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
- the locally relaxed zero-pressure conventional Si observation;
- every pristine supercell specification derived from that observed host;
- every ideal and declared symmetry-broken Si:P and Si:B starting structure;
- every qualified fixed-host pre-relaxation, production relaxation, and
  resulting final-SCF specification;
- optional full ion-and-cell diagnostic specifications and final SCFs;
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
explicit pressure controls. Every neutral Si:P and Si:B role must declare collinear spin
polarization with an absolute spin-channel electron difference of one. Bulk and
nonneutral roles carry their own explicit spin specifications rather than
inheriting a defect value. Defect relaxations and final SCFs must disable both
spatial-symmetry and time-reversal k-point reductions.

The three required defect starts are exact ideal, 0.01 angstrom impurity
translation along host `<100>`, and 0.01 angstrom impurity translation along host
`<111>`. A pre-relaxation uses a lower-cost but reviewed numerical profile only
to obtain a better starting geometry. Its output carries exact lineage into a
production relaxation; its approximate energy cannot eliminate a declared
basin. The composition layer retains all results and identifies the lowest
compatible converged observed basin from separate production final SCFs. It
does not relabel optimizer completion as vibrational proof of a minimum.

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

Tests must cover the full 64/216/512 role matrix, three exact starting basins,
missing roles, exact-record ambiguity, impurity and size mismatch,
charge/electron-count sign and mismatch validation, neutral-only
formation-energy enforcement, required neutral-Si:P and Si:B doublet spin,
symmetry-disable intent, spin mismatch rejection, evidence qualification
failure, chemical-potential provenance, formation-energy sign
convention, threshold boundaries, stable windows, budgets, and deterministic
decision ordering. Repository gates must enforce provider-independent imports
and calculator-free tests.
