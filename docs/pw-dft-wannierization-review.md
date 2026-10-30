# PW-DFT bulk qualification and Wannierization review

## Scope

This is the documentation-only Tranche 1 API/schema/migration review against
`bbb9f1d8110ed9fe3ea1873c2366073c98f48c71`. It reserves no API and authorizes
no calculator execution. Its governing principle is reuse: add only the
composition and provider operations that the repository does not already have.

## Existing capability to reuse

ProjectKoios already provides:

- exact structures, neutral `PseudopotentialFile` requirements, and the
  byte-verifying local `PseudopotentialLibrary` resolver;
- SCF specifications, recipes, workflow definitions, QE projection/execution,
  evidence, and canonical serialization;
- joint cutoff/k-point convergence through `PwDftScfGridConvergenceRecipe`,
  `EnergyGridConvergenceAssessor`, and `PwDftScfConvergenceController`;
- protected relaxation contracts, reusable relaxation composition/workflow,
  QE execution and normalization, and exact relaxed-structure publication;
- generic prepared-input, execution, artifact, normalization, and simulation
  evidence records;
- QE uniform-grid NSCF configuration, execution, saved-state handling, and
  plane-wave-frame extraction;
- QE `pw2wannier90.x` configuration, projection, authenticated staging,
  execution, streams, and AMN/MMN/EIG inspection;
- Wannier90 authentication and parsers for NNKP, EIG, AMN, MMN, `.wout`,
  unitary matrices, disentanglement matrices, and Hamiltonian blocks; and
- `CalculatorExecutor` for separately authorized native processes.

The work therefore does **not** require a second neutral pseudopotential record
or local resolver, a new convergence algorithm, a new k-point model, an
execution framework, an NSCF runner, a `pw2wannier90.x` runner, or a Wannier90
parser. Outward source/catalog discovery and explicitly authorized acquisition
remain a separate missing operational capability when required bytes are not
already present locally.

## Bulk qualification: minimal delta

Bulk qualification composes existing workflows:

```text
S0 -> existing grid assessment + new typed correlation -> Q0@S0
   -> existing relaxation under Q0
   -> candidate S1
   -> existing grid assessment + new typed correlation -> Q1@S1
   -> accept, or re-relax under changed Q1 within the declared budget
```

Required additions are limited to:

1. a provider-neutral coupled plane-wave cutoff policy/realization;
2. a typed structure-scoped SCF grid-correlation record over the existing
   recipe, observations, assessment, and evidence;
3. a pure zero-pressure assessment over an existing relaxation result;
4. an iteration record that references correlated convergence, relaxation,
   publication, and confirmation evidence; and
5. a terminal stable-pair record containing one accepted structure and one
   accepted neutral numerical setting.

The existing grid recipe, assessor, and controller remain unchanged. Their
current observation/assessment records alone are not structure-scoped and are
not sufficient to establish `Q_i@S_i`.

### Neutral cutoff and stable-pair identity

A new neutral cutoff policy/realization must describe physical plane-wave basis
settings without naming QE fields. It contains exactly one positive finite
wavefunction kinetic-energy cutoff and one positive finite density/potential
kinetic-energy cutoff in a declared energy unit, plus an optional neutral
multiple/derivation convention when the second is derived. It is not a
provider-native configuration object.

The terminal stable-pair record must retain exactly:

- one accepted structure reference;
- one existing `PwDftKPointSamplingPolicy` realization;
- one exact neutral coupled-cutoff realization;
- one accepted typed grid-correlation result scoped to that structure;
- a nonempty ordered iteration/evidence history; and
- one accepted terminal disposition.

QE `ecutwfc`, `ecutrho`, and `charge_density_cutoff_ratio` remain in QE
projection and first-party adapter evidence. The adapter proves that exact QE
inputs realize the neutral cutoff record. Every later parent, NSCF, relaxation,
and converter predecessor must correlate to the same neutral setting, preventing
downstream drift without embedding QE policy in a neutral handoff.

The existing cubic convergence coordinate and full k-point policy remain
unchanged. Convergence is rerun after structure change. Noncubic convergence
and independently varying the density/potential cutoff remain outside this
work.

### Typed structure-scoped grid correlation

One new neutral correlation record must bind:

- one exact structure, SCF base request/specification, pseudopotential inventory,
  neutral cutoff realization, full k-point policy, recipe, and assessment policy;
- every existing convergence coordinate/energy observation in source order;
- for every coordinate, exactly one projected SCF request/specification,
  prepared-input identity, selected occurrence, `SimulationEvidenceRecord`,
  normalized-observation byte identity, and provider-adapter mapping identity;
- one unchanged existing `PwDftScfConvergenceAssessment`; and
- exactly one selected production coordinate when the assessment is accepted.

The correlation rejects mixed structures, models, policies, pseudopotentials,
provider cutoff realizations, prepared inputs, occurrences, or evidence. It adds
typed qualification lineage without changing current assessor behavior. The
existing replay evidence's untyped source string is not used as a substitute.

### Zero-pressure assessment

The assessment reuses existing final force, pressure, stress, ionic/cell flags,
completion facts, thresholds, and target. It recomputes each criterion and
returns passed, failed, or inconclusive. Provider completion or optimizer flags
do not independently establish acceptance.

## Wannier route: minimal delta

After stable-pair acceptance, the route has five separately authorized
occurrences:

1. new parent SCF using the existing SCF lifecycle;
2. uniform-grid NSCF using the existing QE NSCF integration;
3. `wannier90.x -pp seed` preprocessing;
4. `pw2wannier90.x` using the existing QE converter runner; and
5. `wannier90.x seed` localization.

The bulk confirmation SCF is predecessor evidence and is not reused as
occurrence 1.

### Missing provider operations

Only three Wannier90 provider additions are required:

1. an immutable native `.win` input model and deterministic renderer for a
   reusable generic non-spin spectral subset; consuming projects supply every
   material-specific structure, projection, window, mesh, and control value;
2. a thin preprocessing wrapper that authenticates inputs/executable, stages an
   occurrence, calls `CalculatorExecutor` with `wannier90.x -pp seed`, captures
   execution evidence, and authenticates one `.nnkp`; and
3. a thin localization wrapper that stages authenticated `.win`, `.nnkp`,
   `.eig`, `.amn`, and `.mmn`, calls `CalculatorExecutor` with
   `wannier90.x seed`, and authenticates configured outputs.

These wrappers encode command lines and native staging only. Existing parsers
remain authoritative for output meaning and dimensions.

### Neutral route records

Reuse `SimulationEvidenceRecord` and `EvidenceArtifactReference`. Begin with
only:

- one route requirement referencing the accepted stable pair, parent/NSCF
  requirements, construction choices, closed artifact profile, and ordered
  five-occurrence dependency; and
- one route result referencing exactly five selected evidence records and the
  normalized lineage/dimensional facts supplied by first-party adapters.

Do not introduce per-stage neutral record classes unless implementation proves
they are necessary for validation.

### Ordinary artifact closure

The first route requires:

```text
preprocessing: exactly 1 NNKP
conversion:    exactly 1 EIG + 1 AMN + 1 MMN
localization:  exactly 1 WOUT plus only declared outputs
```

Existing parsers enforce native dimensions and ordering:

```text
EIG: N_k x N_b
AMN: N_k matrices of N_b x N_p
MMN: N_k x N_n matrices of N_b x N_b
```

UNK and SPN are not part of ordinary closure. Component-operator routes are
deferred.

## Existing QE manifest compatibility

`QeWannier90PlaneWaveArtifactManifest` remains unchanged. It is a specialized
public aggregate that requires UNKs and downstream representation artifacts; it
is not the existing ordinary AMN/MMN/EIG converter observation.

For the first route:

- retain its constructor, verifier, validator, export, and tests;
- do not add optional AMN/MMN fields;
- do not make its UNKs optional;
- do not migrate or deprecate it; and
- use the existing `QePw2Wannier90ArtifactObservation` for ordinary converter
  output.

First-party adapter correlation combines the existing converter observation
with exact execution, parent NSCF, and NNKP identities and rejects mixed
parents, seeds, producers, duplicate selected roles, undeclared retained roles,
or dimensional mismatch. “Undeclared extras” applies to the selected retained
evidence/closed manifest, not arbitrary incidental files in a native work
directory. Wrappers may ignore or separately inventory incidental files but may
not promote them into route evidence.

## Serialization and compatibility

Existing schemas, canonical bytes, constructor behavior, and SHA-256 identities
remain unchanged.

Only the genuinely new neutral cutoff realization, typed grid correlation,
bulk records, and neutral route records receive their own representation and
schema version 1, using existing strict canonical JSON rules. They reference
existing records by representation, schema version, byte size, and SHA-256. No
existing specification, observation, assessment, replay, or evidence bytes are
reinterpreted. No decoder invents a missing cutoff, artifact, occurrence, or
lineage value.

There is no automatic migration. Historical evidence lacking an authenticated
charge-density setting cannot establish a complete stable pair. The specialized
UNK aggregate cannot be losslessly converted to ordinary EIG/AMN/MMN closure
because it lacks AMN/MMN and spans multiple producer stages.

## Ownership boundaries

- Protected core owns existing physical structures, settings, pseudopotentials,
  and generic evidence.
- `projectkoios.simulations.workflows` owns only reusable composition,
  assessments, stable-pair semantics, and route correlation.
- QE/Wannier90 integrations own native models, rendering, command lines,
  staging, execution observations, and parsers; they do not import workflow
  policy.
- First-party `projectkoios.adapters` owns provider/native-to-neutral mapping.
- Repository tools own provider selection, operational configuration, resource
  resolution, authorization requests, invocation, and replay.
- External Workflow infrastructure owns scheduling, retries, cancellation, and
  persistence.

The existing `PseudopotentialLibrary` resolves only exact caller-declared local
bytes; it does not discover source metadata, query a provider catalog, or
acquire an absent artifact. ProjectKoios outward integrations/adapters/tools own
source/catalog metadata discovery, explicitly authorized acquisition, byte-size
and hash authentication, and catalog evidence before constructing or accepting
the existing neutral `PseudopotentialFile` requirement. The neutral workflow
only consumes authenticated exact evidence. This review and its implementation
plan do not themselves authorize network access or acquisition.

## Dependency-ordered implementation plan

1. Freeze the neutral coupled-cutoff realization and typed structure-scoped
   grid-correlation shapes without changing existing SCF schemas or assessors.
2. Implement first-party QE mapping that proves native projected cutoffs realize
   the neutral setting and binds every grid coordinate to exact evidence.
3. Select the production corner from an accepted correlated grid assessment.
4. Add zero-pressure assessment over existing relaxation results.
5. Compose existing convergence and relaxation workflows and emit the stable
   pair.
6. Add outward pseudopotential source/catalog metadata and authorized
   acquisition support needed when exact local bytes are absent, reusing
   `PseudopotentialFile` and `PseudopotentialLibrary`.
7. Add the generic non-spin spectral `.win` model/renderer.
8. Add the two thin Wannier90 wrappers over `CalculatorExecutor`.
9. Add first-party mappings over existing QE/Wannier90 records.
10. Add the minimal five-occurrence requirement/result composition.
11. Add repository tools and calculator-free fake/retained-evidence tests.

Tests must cover exact identities, canonical bytes, structure-scoped typed
correlation, neutral-to-QE cutoff-realization mapping, zero-pressure boundaries,
re-relaxation after changed settings, budget exhaustion, five separate
occurrence authorizations, exact staging/commands, parent/seed correlation,
artifact cardinality/dimensions, selected retry identity, ordinary no-UNK
closure, import boundaries, and unchanged existing APIs.

## Accepted Tranche 1 constraints

The operator accepted these constraints for subsequent implementation review:

1. **Production grid corner:** select the highest tested mesh/cutoff corner from
   an accepted typed grid correlation. The current assessor proves its two
   high-coordinate edges; the assessment alone remains unscoped.
2. **Zero-pressure evidence:** require finite maximum force, scalar pressure,
   and complete stress for variable-cell qualification, with criteria
   recomputed from normalized observations.
3. **First `.win` scope:** support a reusable generic non-spin spectral
   Wannier90 subset. KSD supplies silicon-specific structure, projections,
   windows, k-point mesh, and all scientific values. Unsupported restart, spin,
   and operator extensions fail closed.
4. **Localization outputs:** require `.wout` and `_hr.dat`; require `_u.mat` and
   `_u_dis.mat` only when the declared construction needs them. No undeclared
   retained-evidence roles are permitted; incidental native work-directory
   files are not automatically route defects or evidence.

No decision remains pending for this Tranche 1 review. The existing convergence
algorithm, k-point representation, QE NSCF, QE conversion, Wannier90 parsing,
generic executor, and specialized manifest remain reused. Pseudopotential
source/catalog and acquisition mechanics remain outward ProjectKoios
implementation work and require separate explicit network authorization when
exercised.
