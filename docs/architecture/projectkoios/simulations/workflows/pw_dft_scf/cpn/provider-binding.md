# Provider proposal: SCF saved-state candidate and canonical child export

## 0. Status and exact scope

This is a **design/review proposal only**. It does not implement an API, migrate a
provider, change a dependency, authorize an effect, execute a calculator, create
a commit, push, release, or establish compatibility.

The proposal is consumer-led by Si-VC/ksdft2effmass. Generic Workflow and the
simulations provider must implement conforming boundaries; they do not impose a
second acceptance gate over the selected consumer contract.

Exact conformance inputs reviewed for this proposal:

| Input | Identity |
|---|---|
| Generic Workflow owner conformance target | `projectkoios.workflow.cpn-bindings@0.1.0`; Git `9ec0944dad3af1706edf01101e443e244da22ef5`; SHA-256 `e6428a8b0d8a47d4f9a6596300fe5ccc65bb16c12e1cc8ffe64884720bd513c2` |
| Si-VC Workflow binding profile | Git `4ef67e49f11a00e66f5c6ed6f4f2d72eb441505a`; SHA-256 `e3496191b7299b2bdba11ba3ca4679a0eb80a421bd076eac1a7a8fdc3344dd06` |
| Si-VC SCF saved-state lineage contract | Git `4ef67e49f11a00e66f5c6ed6f4f2d72eb441505a`; SHA-256 `e49bb8197069d8788aa9382ff823506471c2665bd605016669123bb2f2630183` |
| Simulations preflight | SHA-256 `728862e4a68fb0cac85109c1e1abe84a54e45ca1a923b0c08fe6a7a88a152fb3` |
| Simulations source revision | Git `33b7170fffb289f4e7205c63b7789a4f9468a74b` |
| Authoritative SCF topology source | `src/python/projectkoios/simulations/workflows/pw_dft_scf/cpn/net.py`, SHA-256 `4d580f686382851b32fccfbb7aa775782e3c44daf9e6efcf6d1cd95ca9d2d563` |
| Historical topology provenance | Applications Git `416be52d539bfbffdbc8a27bd8e13de65404821b`, blob `7d6600ba8cbf0b079871d8c325b352bbf22d6afd` |
| SNAKES source dependency | `projectkoios-snakes` Git `c959528c3b35c12563b7ba291ca036e1ebb58f7e` |
| Saved-state implementation evidence | `saved_state.py`, SHA-256 `137fc6f350b4728918b0ea44935f0aad38ccd28fc276f9e0f134d2e0e2878962` |
| Existing evidence record evidence | `evidence/record.py`, SHA-256 `9074d59037ba57be151d89d04d1255013050e545ed352b908a2acd4c469a8b3c` |

The exact owner and consumer successor bytes above were independently rechecked
before this document was committed. This provider document binds those
already-derived owner and consumer digests in one direction. The consumer core
and lineage documents do not embed this later provider-document digest; a
separate later review record binds the exact owner, consumer, lineage, and
provider documents without a content-hash cycle.

## 1. Migration decision

This proposal preserves the existing authoritative twelve-place/eight-transition
SNAKES net byte-for-value and behavior-for-behavior. It does not add a place,
transition, guard, arc, inscription, or second SCF topology.

Two provider boundaries are added around, not inside, that net:

1. a deterministic exporter/adapter translates a constructed authoritative net
   into canonical flat CPN IR and emits golden parity evidence; and
2. after an existing successful terminal outcome is retained, a provider
   adapter assembles a separately retained candidate saved-state handoff from
   the exact already-retained execution, input, manifest, saved-state, and
   terminal evidence.

The long-term definition producer remains `projectkoios-simulations`. Generic
Workflow validates, links, and executes the exported definition without
importing simulations or copying topology. The current local runtime and handler
are compatibility evidence and migration bridges, not permanent execution
owners.

Required migration order:

1. bridge plus golden parity;
2. payload codec/reference binding;
3. hierarchical nested route;
4. later runtime-segment persistence/replay integration; and
5. retirement of the compatibility runtime last.

## 2. Provider-owned candidate saved-state handoff

### 2.1 Proposed contract identities

| Concept | Proposed identity |
|---|---|
| Schema | `projectkoios.integrations.quantumespresso.qe-pw-scf-saved-state-candidate:1` |
| Codec | `projectkoios.integrations.quantumespresso.qe-pw-scf-saved-state-candidate-json:1` |
| Media type | `application/vnd.projectkoios.qe-pw-scf-saved-state-candidate.v1+json` |
| Candidate identity prefix | `projectkoios.integrations.quantumespresso.qe-pw-scf-saved-state-candidate:1:` |
| Workflow payload-color role | `qe-pw-scf-saved-state-candidate-reference` |

Names are conceptual until implementation is separately authorized, but the
field set and identity rules below are closed for this proposal.

### 2.2 Closed version-one document

The provider-owned canonical document has exactly these top-level fields. Its
fixed header values are
`schema_identity = "projectkoios.integrations.quantumespresso.qe-pw-scf-saved-state-candidate:1"`,
`schema_version = 1`, and
`candidate_kind = "qe-pw-scf-saved-state"`.

```text
schema_identity
schema_version
candidate_kind
producer
workflow
subject
input_lineage
success_evidence
saved_state
terminal
```

#### `producer`

| Field | Requirement |
|---|---|
| `integration_identity` | Literal `quantum-espresso`; not an executable path |
| `adapter_identity` | Exact candidate-assembler implementation identity |
| `adapter_version` | Immutable implementation/version descriptor |
| `source_revision` | Exact simulations source revision |

#### `workflow`

All values are bounded opaque Workflow-owned identities, not identities minted
by simulations:

| Field | Correlation |
|---|---|
| `child_export_identity` | Exact immutable linked child export whose terminal-delivery requirements govern this candidate |
| `child_execution_plan_identity` | Exact linked child plan |
| `child_run_identity` | Exact child Workflow run |
| `child_net_instance_identity` | Exact nested child instance |
| `calculator_request_identity` | Exact retained request that led to the calculator occurrence |
| `calculator_transition_occurrence_identity` | Exact protected calculator occurrence |
| `calculator_plan_identity` | Exact retained execution plan for that occurrence |
| `calculator_effect_intent_identity` | Exact calculator effect intent |
| `calculator_attempt_identity` | Exact attempt whose bytes are represented |
| `calculator_dispatch_authorization_identity` | Attempt-bound authority admission |
| `calculator_execution_evidence_identity` | Exact retained successful execution evidence |

#### `subject`

| Field | Requirement |
|---|---|
| `evaluation_id` | Existing calculator-neutral SCF evaluation identity |
| `task_id` | Existing child task identity |
| `simulation_specification_reference_identity` | Reference to exact neutral specification bytes |

#### `input_lineage`

| Field | Requirement |
|---|---|
| `calculator_input_record_reference_identity` | Reference to exact `CalculatorInputRecord` bytes |
| `calculator_input_record_sha256` | Exact canonical record digest |
| `rendered_input` | Closed record: role, safe basename, byte size, SHA-256 |
| `structure` | Closed record: structure identity, representation, schema version, byte size, SHA-256, payload-reference identity |
| `executable` | Closed record: program `pw.x`, reported version, byte size, SHA-256, immutable artifact/reference identity; no path |
| `pseudopotentials` | Nonempty ordered closed records: element symbol, stable file identity, safe filename, format, byte size, SHA-256, provenance identity, payload-reference identity |

Pseudopotential order is the rendered calculator-input declaration order. It is
not filesystem enumeration order or lexicographic repair.

#### `success_evidence`

| Field | Requirement |
|---|---|
| `calculator_execution_record_reference_identity` | Exact retained terminal process record |
| `simulation_evidence_reference_identity` | Exact provider evidence projection |
| `normalized_observation_reference_identity` | Exact normalized SCF observation |
| `execution_status` | Literal `succeeded` |
| `returncode` | Exact integer `0` |
| `provider_completed` | Exact Boolean `true` |
| `calculation_converged` | Exact Boolean `true` |

These Booleans describe provider evidence. They do not assert Si-VC acceptance.

#### `saved_state`

| Field | Requirement |
|---|---|
| `calculation` | Literal `scf` |
| `prefix` | Exact safe QE prefix |
| `manifest_reference_identity` | Exact Workflow reference identity for manifest bytes |
| `manifest_artifact_identity` | Immutable artifact identity from that six-field reference |
| `manifest_sha256` | SHA-256 of exact manifest bytes |
| `manifest_byte_size` | Positive exact byte size |
| `artifact_set_identity` | Immutable artifact-store collection identity for the complete manifest-declared set; no path |
| `artifact_count` | Exact manifest entry count |
| `total_byte_size` | Exact sum of manifest entry sizes |
| `source_verification_evidence_identity` | Evidence that every and only declared source regular file was verified |

#### `terminal`

| Field | Requirement |
|---|---|
| `child_definition_identity` | Exact nominal exported child definition |
| `terminal_transition_occurrence_identity` | Exact `accept_analysis` occurrence in the child run |
| `terminal_place_identity` | Literal `terminal_outcome` |
| `terminal_classification` | Literal `succeeded` |
| `terminal_outcome_reference_identity` | Exact retained `PwDftScfWorkflowSucceeded` payload reference |
| `terminal_history_head_identity` | Exact child history head at terminal commit |

The handoff is assembled only after the pre-existing terminal outcome has been
retained. Therefore it may safely reference that outcome. The terminal outcome
does not reference the later handoff, so no content-identity cycle exists. A
later Workflow delivery record references both.

### 2.3 Identity and codec derivation

The pure owner codec encodes the closed typed record with the exact private
canonical control-JSON profile selected by owner successor
`e6428a8b0d8a47d4f9a6596300fe5ccc65bb16c12e1cc8ffe64884720bd513c2`:

- UTF-8, no BOM;
- one object, exact keys, lexical key order;
- compact separators;
- no leading/trailing bytes or trailing newline;
- strings, signed 64-bit integers, exact Booleans, arrays, objects, and null only;
- no binary64 numbers, `NaN`, infinity, duplicate keys, unknown keys, or numeric
  strings substituted for integers.

#### Exact lexical and size profile

Canonical validation applies these exact version-one bounds before typed
construction and repeats them after re-encoding:

| Value class or field | Exact bound |
|---|---|
| Complete canonical candidate document | `1..262144` bytes; maximum JSON nesting depth `6`; exactly the closed top-level and nested keys declared here |
| All Workflow, payload-reference, schema, codec, owner, child-export, plan, definition, operation, evidence, history-head, immutable artifact, artifact-set, and provenance identities | `1..512` ASCII bytes; no control, DEL, leading/trailing whitespace, NUL, or line break |
| Artifact and artifact-set identities | Identity bound above, and must not begin with `/`, `~/`, `\\`, `file:`, or an ASCII drive-letter plus `:`; no `.` or `..` path-segment interpretation is permitted |
| `schema_identity`, `candidate_kind`, integration identity, literal program, calculation kind, execution status, terminal place/classification | Exact literals declared by this schema; no aliases or case folding |
| `source_revision` | Exactly 40 lowercase hexadecimal digits for the selected Git profile |
| Adapter identity and version | Identity bound above; version additionally `1..128` printable ASCII bytes |
| `evaluation_id` | `1..128` ASCII bytes; lowercase slug `[a-z0-9]+(?:-[a-z0-9]+)*` |
| `task_id` | `1..256` printable ASCII bytes; stripped; controls and DEL forbidden |
| QE `prefix` | `1..128` ASCII bytes; `[A-Za-z0-9][A-Za-z0-9_.-]{0,127}` |
| Safe filename | `1..255` ASCII bytes; `[A-Za-z0-9][A-Za-z0-9_.-]{0,254}`; not `.` or `..`; no slash or backslash |
| Role | `1..64` ASCII bytes; lowercase slug `[a-z0-9]+(?:-[a-z0-9]+)*` |
| Program/version/format/representation text | `1..128` printable ASCII bytes; stripped; controls and DEL forbidden |
| Structure and stable pseudopotential identities | Identity bound above |
| Element symbol | `1..2` ASCII bytes; `[A-Z][a-z]?` |
| SHA-256 | Exactly 64 lowercase hexadecimal ASCII digits |
| Schema versions and artifact counts | Exact signed integers, never Booleans; schema versions `1..2147483647`; counts `1..4096` unless a smaller collection bound below applies |
| Byte sizes | Exact signed integers, never Booleans; `1..9223372036854775807`; additionally no greater than the referenced schema/color limit |
| Candidate `pseudopotentials` | `1..256` entries in rendered-input order; unique element symbol, stable identity, and filename; each entry has the exact closed field set |
| Manifest artifacts | `1..4096` entries and total declared bytes `1..68719476736` (64 GiB), matching the current saved-state verifier limits |
| Every other object | Exactly one instance with its declared closed keys; no optional unknown member |
| Every other array | Prohibited in schema version one |

All candidate strings are ASCII by design; there is no human prose field in
this record. A future need for Unicode text requires a schema-version change and
an explicit normalization decision. Collection bounds apply both while parsing
and after cross-record resolution. The lower manifest-role invariants (one
QEXSD, one charge density, at least one wavefunction, and matching
pseudopotentials) remain stricter than the generic `1..4096` artifact-count
bound.

The candidate identity is not embedded in the document:

```text
candidate_digest = sha256(canonical_candidate_bytes)
candidate_identity =
  "projectkoios.integrations.quantumespresso."
  "qe-pw-scf-saved-state-candidate:1:" + candidate_digest
```

The pure codec returns bytes plus metadata:

```text
payload_identity = candidate_identity
schema_identity = projectkoios.integrations.quantumespresso.
                  qe-pw-scf-saved-state-candidate:1
media_type = application/vnd.projectkoios.
             qe-pw-scf-saved-state-candidate.v1+json
```

An authorized outer artifact operation retains those exact bytes and returns an
immutable artifact identity. A pure assembler then creates the exact six-field
`WorkflowDomainPayloadReference`, computing size and digest from the supplied
bytes. The provider codec must not read a store, fabricate an artifact identity,
or accept a caller-claimed digest or size.

The Workflow reference identity remains distinct from the candidate identity,
manifest digest, artifact-set identity, execution-evidence identity,
child-export identity, and terminal-outcome reference identity. Because
`child_export_identity` is an encoded candidate field, changing it changes the
canonical candidate bytes, candidate identity, and assembled Workflow reference
identity even when every other field remains equal.

### 2.4 Candidate invariants

A candidate is valid only if all of the following hold:

1. Every Workflow identity exists in one retained acyclic chain for the same
   immutable child export, child execution plan, child run, net instance,
   calculator occurrence, plan, intent, attempt, authorization, and successful
   evidence. The linked plan identifies that exact export; a nominal child
   definition or matching plan name is insufficient.
2. The authority is exact-attempt and exact-intent authority. Possession of the
   candidate never grants later execution or staging authority.
3. The execution record has status `succeeded` and return code zero; stdout or a
   `JOB DONE` string alone is insufficient.
4. The normalized observation is correlated to the same task and retained
   native output and has `completed == true` and `converged == true`.
5. The terminal outcome is `PwDftScfWorkflowSucceeded`, belongs to the same
   child export/plan/run/instance, contains the same
   evaluation/task/observation lineage, was emitted by `accept_analysis`, and is
   the exact terminal history head. The candidate `child_export_identity` must
   equal the export selected by the terminal delivery and linked child plan.
6. The manifest calculation is `scf`; its input SHA-256 equals the rendered SCF
   input artifact; its structure identity/digest equal the referenced structure;
   and its executable digest/version equal the referenced executable.
7. The manifest pseudopotential set equals the rendered input requirements and
   candidate list one-for-one by symbol, filename, byte size, and SHA-256.
8. Each manifest pseudopotential entry has the exact matching saved-state
   artifact required by existing `QeSavedStateManifest` validation.
9. The manifest contains exactly one QEXSD artifact, exactly one charge-density
   artifact, at least one wavefunction artifact, and every inventoried artifact
   has a safe source-root-relative POSIX path.
10. The artifact set contains every and only manifest-declared regular file;
    every byte size and digest was checked; links, traversal, special files,
    undeclared files, and mutable directory locators fail closed.
11. `artifact_count` and `total_byte_size` equal the manifest exactly and remain
    within provider and Workflow color-binding bounds.
12. No field contains a machine path, credential, executable command, mutable
    store handle, or provider-native live object.
13. Changed bytes or any changed lineage/correlation field, including
    `child_export_identity`, change the candidate identity; reordering a
    semantically ordered pseudopotential list also changes it.
14. The record asserts provider candidacy only. It does not assert campaign
    acceptance, scientific adequacy, publication, or authorization.
15. Candidate retention failure, missing terminal evidence, ambiguous execution,
    manifest failure, or cross-record mismatch prevents a success handoff and
    therefore prevents parent nested-route delivery.

### 2.5 Generation protocol without changing the child net

1. Generic Workflow retains the exact child export and execution plan, request,
   occurrence, plan, attempt, authority, execution evidence, and child run
   correlations.
2. The QE provider completes the already-authorized calculator effect.
3. Provider code inventories and verifies the saved-state tree with the existing
   strict manifest contract, then retains the immutable manifest and artifact
   set outside the CPN kernel.
4. Existing output analysis produces the existing `PwDftScfOutputAnalyzed`.
5. The unchanged `accept_analysis` transition produces the existing
   `PwDftScfWorkflowSucceeded` in `terminal_outcome`.
6. Workflow retains and references that terminal outcome and history head.
7. The outer QE provider adapter pure-encodes the candidate from already-retained
   references and correlation; the artifact boundary retains it; the pure
   assembler creates its six-field Workflow reference.
8. The exact owner `WorkflowTerminalDeliveryRequirement` for the existing
   success terminal port declares one
   `WorkflowTerminalCompanionEvidenceRequirement` with:
   - identity
     `projectkoios.integrations.quantumespresso.qe-pw-scf-saved-state-candidate-companion:1`;
   - signed ordinal `0`;
   - evidence role `qe-pw-scf-saved-state-candidate-reference`;
   - owner `projectkoios-simulations`;
   - the exact candidate schema, codec, and media type from section 2.1;
   - maximum payload bytes `262144`;
   - minimum and maximum reference cardinalities both `1`;
   - production phase `post_terminal_pre_delivery_retained`;
   - correlation predicate descriptor
     `projectkoios.integrations.quantumespresso.qe-pw-scf-saved-state-candidate-correlation:1`,
     which compares decoded child export, child plan, run, net instance,
     terminal classification, terminal outcome, terminal history head,
     calculator occurrence/attempt/authority/evidence, manifest, evaluation, and
     task identities against the exact delivery and retained Workflow sources;
   - requirement contract version `1`.
   The enclosing success requirement has maximum total companion count `1` and
   uses the owner contract's canonical mapper ordering. Every existing known-
   failure classification has its own delivery requirement with an explicit
   empty companion tuple and maximum total companion count `0`.
9. The runtime admits success delivery only after retaining and verifying the
   canonical ordered pair `(terminal_outcome_reference,
   candidate_handoff_reference[0])` and their common child-export/plan,
   run/instance/occurrence/evidence chain. The pure output mapper then creates
   the Si-VC child outcome reference. The campaign separately decides whether to
   create an accepted-parent record.

The requirements are semantic export closure. Changing role, ordinal, schema,
codec, media type, bound, cardinality, phase, correlation predicate, terminal
classification, or ordering changes child export/plan and parent plan
identities. The requirements contain descriptors, never actual future
references, and do not name their enclosing export/plan identity. The durable
`WorkflowTerminalDelivery` names the already-derived export/plan, primary
terminal reference, canonical companion sequence, terminal history head, and
parent reservation, but not the future parent firing. This is acyclic and does
not add or mutate a CPN token, place, arc, transition, or marking.

A post-terminal candidate assembly failure is operational/reconciliation
failure. It must not rewrite the child outcome or fabricate parent firing.

## 3. Deterministic SNAKES-to-canonical child export

### 3.1 Export profile identity

Proposed conceptual profile:

```text
projectkoios.simulations.pw-dft-scf.snakes-canonical-export:1
```

It targets the canonical flat-definition and execution-profile contracts in
owner successor
`e6428a8b0d8a47d4f9a6596300fe5ccc65bb16c12e1cc8ffe64884720bd513c2`.
No digest for the compiled canonical definition, execution plan, export, or
evidence binding is claimed until an authorized implementation produces and
independently verifies golden bytes.

### 3.2 Authoritative topology inventory

The exporter must derive this inventory by traversing a constructed
`build_dft_pw_scf_net(evaluation_id)` object. It must not use this table as a
second executable definition.

Places, in canonical identity order:

```text
analysis_action
output_analyzed
registration_action
request
submission_action
task_completed
task_failed
task_registered
task_submitted
task_waiting
terminal_outcome
workflow_start
```

Transitions, in canonical identity order:

```text
accept_analysis
accept_analysis_failure
accept_completion
accept_failure
accept_registration
accept_submission
reject_analysis
start_workflow
```

The export must preserve the source semantics:

| Transition | Inputs | Guard | Output |
|---|---|---|---|
| `start_workflow` | consume `workflow_start:start`; read `request:request` | true | `registration_action = RegisterPwDftScfTask(start.evaluation_id)` |
| `accept_registration` | consume `registration_action:action`, `task_registered:registered` | equal evaluation IDs | `submission_action = SubmitPwDftScfTask(registered.task_id)` |
| `accept_submission` | consume `submission_action:action`, `task_submitted:submitted` | equal task IDs | copy `submitted` to `task_waiting` |
| `accept_completion` | consume `task_waiting:waiting`, `task_completed:completed` | equal task IDs | construct `AnalyzePwDftScfOutput(completed.task_id, completed.output_artifact_id)` |
| `accept_analysis` | consume `analysis_action:action`, `output_analyzed:analyzed`; read `request:request` | task IDs equal and observation completed and converged | construct existing successful result/outcome |
| `reject_analysis` | same inputs/read arc | task IDs equal and not(completed and converged) | existing `scf-not-complete-and-converged` failure |
| `accept_analysis_failure` | consume `analysis_action:action`, `task_failed:failed`; read `request:request` | task IDs equal | existing failure with event code/message |
| `accept_failure` | consume `task_waiting:waiting`, `task_failed:failed`; read `request:request` | task IDs equal | existing failure with event code/message |

The exporter must also derive and preserve all twelve `Instance` color checks,
the terminal union/subtyping rule, variables, read-versus-consume arcs, output
inscriptions, literal strings, Boolean logic, and reviewed constructor mappings.

### 3.3 Stable topology versus initial marking

The source constructor currently accepts `evaluation_id` and injects two initial
tokens. The adapter must separate:

- one stable topology export independent of `evaluation_id`; and
- one initial-marking constructor descriptor that, from one validated child
  input, creates exactly:
  - `PwDftScfWorkflowStart(evaluation_id)` at `workflow_start`; and
  - `PwDftScfRequestReference(evaluation_id)` at `request`.

Two different evaluation IDs must produce byte-identical canonical topology and
different canonical initial-marking identities. The input mapping must prove the
two generated evaluation IDs are equal. Parameter values must never silently
redefine the child plan.

### 3.4 Translation rules

The owner-controlled exporter/adapter must:

1. construct only the authoritative source factory from the exact retained
   source revision and SNAKES revision
   `c959528c3b35c12563b7ba291ca036e1ebb58f7e`;
2. traverse the constructed SNAKES places, transitions, `Instance` checks,
   arcs, variables, inscriptions, guards, and initial tokens; a copied inventory,
   repository source file, `repr`, PNML, pickle, or Python bytecode is never an
   executable semantics source;
3. obtain each constructed `snakes.nets.Expression` text only through
   `str(expression)`, whose exact behavior is pinned by the SNAKES revision
   above, and reject an expression object from any other implementation or
   revision. The stripped UTF-8 text must contain `1..4096` bytes, the parsed AST
   at most 128 nodes and depth 16, an attribute path at most three fields, and a
   call at most three positional arguments;
4. parse that exact expression text with
   `ast.parse(expression_text, filename="<projectkoios-scf-expression>",
   mode="eval", type_comments=False, feature_version=(3, 14), optimize=0)`
   under grammar profile `python-ast-eval:3.14`; syntax failure,
   parser-version mismatch, bound excess, or a non-`ast.Expression` root fails
   closed. Parsing never evaluates or compiles the expression;
5. admit only `ast.Expression`, `ast.Name`, `ast.Attribute`, `ast.Constant`,
   `ast.Call`, `ast.BoolOp` with `ast.And` and two or three operands,
   `ast.UnaryOp` with `ast.Not`, and an unchained `ast.Compare` with exactly one
   `ast.Eq`. An `ast.Constant` must be an exact built-in Boolean or string
   required by the reviewed topology; integers, floats, bytes, `None`, ellipsis,
   and subclasses are rejected. Context and operator marker nodes are admitted
   only as required by those parents. Every other node, operator, keyword
   argument, starred argument, chained comparison, subscript, collection
   literal, comprehension, lambda, named expression, conditional, formatting
   expression, arithmetic expression, or dynamic call fails closed;
6. admit `ast.Name` leaves only when they are transition-declared variables or
   one of these exact constructor names and arities already installed in
   `net.globals`: `RegisterPwDftScfTask`/1, `SubmitPwDftScfTask`/1,
   `AnalyzePwDftScfOutput`/2, `PwDftScfResult`/3,
   `PwDftScfWorkflowSucceeded`/1, and `PwDftScfWorkflowFailed`/3. Calls must
   target a bare admitted constructor name; attribute calls and all other call
   targets fail closed;
7. admit attribute paths only from a transition-declared variable and only from
   this reviewed set:
   `start.evaluation_id`, `request.evaluation_id`, `action.evaluation_id`,
   `action.task_id`, `registered.evaluation_id`, `registered.task_id`,
   `submitted.task_id`, `waiting.task_id`, `completed.task_id`,
   `completed.output_artifact_id`, `analyzed.task_id`,
   `analyzed.observation`, `analyzed.observation.completed`,
   `analyzed.observation.converged`, `failed.task_id`, `failed.code`, and
   `failed.message`. Dunder names or attributes and every undeclared path fail
   closed;
8. lower the admitted Python AST directly to the owner canonical symbolic AST of
   variable, field projection, exact literal, closed record construction,
   Boolean `and`, Boolean `not`, and equality nodes. `ast.dump`, the original
   expression text, and parser object identities are not canonical topology
   bytes;
9. map each Python domain type and constructor to a stable owner schema/operation
   identity, never to a mutable import path;
10. encode small child control records in the exact admitted CPN value profile;
    large/provider payloads and the saved-state candidate remain six-field
    references resolved outside the kernel;
11. represent the normalized observation by an immutable reference plus the
    exact bounded guard facts (`task_id`, `completed`, `converged`) so the kernel
    never decodes scientific payloads during enablement;
12. represent the current output artifact identifier through an immutable
    artifact-reference adapter for canonical execution; never export a machine
    path;
13. sort canonical definitions by semantic identity and define an explicit
    ordering for arcs and fields; source iteration, hash seed, address, and
    process locale must not affect bytes;
14. bind all of the following into `WorkflowCpnExecutionProfile` and therefore
    the compiled child plan: expression-text surface identity
    `projectkoios.simulations.snakes-expression-text:1`, grammar identity
    `python-ast-eval:3.14`, parser/lowering identity
    `projectkoios.simulations.pw-dft-scf.python-ast-lowering:1`, exporter identity
    `projectkoios.simulations.pw-dft-scf.snakes-canonical-export:1`, admitted
    value model, decoder, validators, evaluator, complete binding enumerator,
    binding ordering, unique-binding selector, external-output validator, and
    firer;
15. retain the exact Python implementation/version and SNAKES revision used as
    export evidence. A parser, grammar, whitelist, attribute-path, constructor,
    or lowering change changes its implementation/profile identity and child
    plan even if resulting nominal names appear unchanged;
16. preserve current `drain_unique` semantics: zero enabled bindings pauses,
    exactly one fires, and more than one transition or binding fails closed;
17. emit topology bytes, initial-marking bytes, execution-profile identity,
    child execution-plan closure, child export, and a separate evidence binding;
18. never call a provider, artifact resolver, worker, filesystem, clock, network,
    calculator, or owner payload codec inside canonical CPN enablement/firing;
    and
19. prove golden parity against the source SNAKES net before the export is
    eligible for linking.

The admitted constructed `Expression` text is the sole version-pinned parsing
input. This narrow exception does not authorize parsing a repository source
file, `repr`, PNML, pickle, bytecode, arbitrary callback, or unconstructed text
as topology. The adapter may decode and validate retained payloads before
marking admission and may encode outputs after pure firing. Those are outer
adapter phases, not guard callbacks.

### 3.5 Proposed `WorkflowChildDefinitionExport` values

| Export field | Proposed provider value |
|---|---|
| Owner | `projectkoios-simulations` |
| Workflow family | `projectkoios.simulations.workflows.pw_dft_scf` |
| Source definition | Exact factory/source revision and source SHA-256 above |
| Nominal flat definition | `dft_pw_scf` |
| Canonical representation | Owner-target profile plus generated digest; not yet available |
| Child execution plan | Generated closed plan identity/digest; not yet available |
| CPN execution profile | Generated exact profile identity; not yet available |
| Initial marking constructor | Two-token constructor described in 3.3 |
| Input ports | Atomic initial-input mapping to `workflow_start` and `request` |
| External event ports | `task_registered`, `task_submitted`, `task_completed`, `task_failed`, `output_analyzed` |
| Action ports | `registration_action`, `submission_action`, `analysis_action` |
| Terminal port | `terminal_outcome` |
| Terminal classifications | success and known failure from existing outcome union |
| Success companion evidence | Amended owner companion descriptor: exactly one QE candidate handoff reference at signed ordinal `0` for success; exact schema/codec/media/correlation predicate; zero companions for known failure; separate from the CPN token |
| Child cardinality | Exactly one, ordinal signed integer `0`, enforced by parent binding |
| Protected effects | Registration/provider effect as configured; calculator submit; retained-artifact analysis; authority remains Workflow-owned |
| Cancellation declaration | Exact U3 capability: no cancellation input port or cancelled terminal classification; no in-net cancellation; bounded Workflow reconciliation containment only |
| Reconciliation declaration | Workflow-owned; no duplicate child instance or automatic redispatch |
| Exporter revision | Exact future implementation identity; unavailable while unimplemented |

The initial port is a mapping descriptor that atomically initializes two exact
places. It does not add a place or change the source net.

### 3.6 Golden fixture layout

Proposed provider-owned fixture root:

```text
tests/fixtures/workflows/pw_dft_scf/canonical-export/v1/
  source.json
  canonical-flat-definition.json
  cpn-execution-profile.json
  child-execution-plan.json
  child-export.json
  child-export-evidence-binding.json
  initial-markings/evaluation-a.json
  initial-markings/evaluation-b.json
  scenarios/*.json
  expected-digests.json
```

These are future output paths, not authorized files. The canonical definition is
exporter output and evidence, not hand-maintained executable topology. The
parent repository may retain only identities/references and must not copy it.

### 3.7 Required golden parity vectors

1. Source commit, source-file SHA-256, historical provenance, and SNAKES commit
   match the declared export inputs.
2. Source traversal finds exactly 12 places and 8 transitions with the exact
   derived types, arcs, guards, variables, expressions, and constructor set.
   Every constructed expression is obtained through the pinned `str(Expression)`
   surface, parsed under `python-ast-eval:3.14`, admitted by the exact whitelist,
   and lowered to the expected canonical symbolic AST.
3. Two evaluation IDs yield identical canonical topology bytes/digest and
   distinct correct initial markings.
4. Canonical export is byte-identical across process, hash seed, locale, and
   repeated construction.
5. Successful trace parity:
   `start_workflow`, `accept_registration`, `accept_submission`,
   `accept_completion`, `accept_analysis`, with equivalent existing success
   outcome.
6. Each incomplete/unconverged Boolean combination takes `reject_analysis` with
   the exact code/message.
7. Failure while waiting takes `accept_failure`; failure while analyzing takes
   `accept_analysis_failure`; exact code/message propagation is preserved.
8. Mismatched evaluation/task identities do not enable the correlated
   transition and the boundary token remains unconsumed.
9. Duplicate matching events or another ambiguous binding cause both the local
   bridge and canonical selector to fail closed rather than choose by accident.
10. The request `Test` arcs preserve the request token through every terminal
    transition.
11. Invalid event type/color, unknown constructor, unsupported SNAKES node,
    unexpected global, path-bearing canonical artifact value, or payload decode
    attempt inside a guard fails closed. Wrong SNAKES/Python version, syntax
    error, unlisted AST node/operator/attribute path, dynamic or attribute call,
    keyword/star argument, wrong constructor arity, dunder access, chained
    comparison, subscript, comprehension, lambda, repository-source parsing,
    `repr`, PNML, pickle, or bytecode input also fails closed.
12. Every semantic mutation of a place, color, transition, arc kind, variable,
    guard, inscription, literal, constructor mapping, expression-text surface,
    parser, grammar, AST whitelist, attribute-path set, AST lowering, selector,
    evaluator, or firing rule changes the applicable canonical/profile/plan
    identity.
13. Marking-only subject changes do not change topology identity.
14. Source-order-only permutations normalize to identical canonical bytes;
    semantically ordered list changes do not.
15. No exporter, parity, replay, or fixture generation invokes a provider,
    worker, calculator, network service, or execution authority.
16. Parent binding contains child/export/plan identities and mapper descriptors
    but no copied child topology.
17. A success terminal outcome without the exact correlated candidate handoff
    cannot produce the Si-VC parent output; wrong child export, child plan, run,
    instance, occurrence, attempt, authority, evidence, manifest, terminal
    classification, outcome, or history head fails closed.
18. Candidate handoff creation failure leaves the child terminal evidence intact
    but produces no parent firing and enters operational reconciliation.
19. Candidate canonical encode/decode/reference assembly passes stable-identity,
    unknown/duplicate/missing key, noncanonical bytes, Boolean-as-number,
    changed/wrong `child_export_identity`, digest, size, path, and bound tests. Every lexical/document/collection bound
    in section 2.3 is tested at lower bound, upper bound, and one value beyond
    each applicable side; aggregate document size and nesting depth are tested
    independently of per-field validity.
20. Child-export, manifest/source artifact, undeclared file, link, traversal,
    executable, input, structure, pseudopotential, terminal-outcome, or
    execution-evidence tamper or mismatch prevents handoff.
21. The same candidate bytes retained under a different immutable artifact
    identity keep the candidate payload identity but change the six-field
    Workflow reference identity; neither is silently substituted.
22. Candidate evidence never satisfies Si-VC acceptance; only the separate
    ksdft2effmass acceptance transition may emit an accepted-parent record.
23. Outer replay accepts unchanged Slice A first, verifies later-segment bridges,
    resolves and validates retained candidate/manifest/outcome bytes outside the
    kernel, then replays pure child CPN semantics without effects.
24. Quiescence is withheld while handoff assembly/delivery, an attempt,
    cancellation, process, ambiguity, invalid evidence, or partial application
    remains unresolved.

## 4. Owner boundaries

### `projectkoios-simulations`

- Remains authoritative owner/producer of the 12/8 SCF source definition,
  calculator-neutral actions/events/outcomes, deterministic exporter, export
  fixture, and parity evidence.
- Does not schedule, mint Workflow runtime identities, admit authority, resolve
  retries, or own campaign acceptance.
- Does not move the source definition into Generic Workflow.

### Quantum ESPRESSO outward integration

- Owns the candidate schema/codec, executable/input/pseudopotential/native
  correlation, saved-state manifest and artifact-set verification, and candidate
  assembler.
- Produces mechanical provider evidence only.
- Does not decide Si-VC scientific acceptance and does not expose local paths.

### Generic Workflow

- Owns canonical contract validation/linking, plan and deployment identities,
  run/net-instance/request/occurrence/attempt/authority/evidence identities,
  artifact-reference admission, persistence, nested reservation/delivery,
  cancellation, reconciliation, replay, and quiescence.
- Executes the exported definition without importing simulations and without
  copying its topology.
- Does not manufacture provider evidence or campaign acceptance.

### `ksdft2effmass`

- Owns the Si-VC parent CPN, exact child requirement/outcome mapping, scientific
  role/policy, provider-candidate assessment, accepted-parent schema, staging
  requirement, and final scientific disposition.
- Consumes the unchanged candidate reference; it does not reinterpret native QE
  directories or mint child runtime identities.

### Artifact/worker boundary

- Retains exact immutable bytes and artifact sets, supplies immutable artifact
  identities, resolves private locators only inside authorized isolated workers,
  and returns verification evidence without paths in canonical events.
- Retention or staging authority never comes from a CPN token or candidate.

## 5. Selected corrections, unresolved dependencies, and stop conditions

### U1 — companion handoff in terminal mapping (selected and owner-specified)

Owner successor `projectkoios.workflow.cpn-bindings@0.1.0`, exact SHA-256
`e6428a8b0d8a47d4f9a6596300fe5ccc65bb16c12e1cc8ffe64884720bd513c2`,
defines `WorkflowTerminalDeliveryRequirement` and
`WorkflowTerminalCompanionEvidenceRequirement` with exact role/schema/codec/media,
bounds, cardinality, production phase, canonical ordering, correlation,
delivery, replay, ambiguity, and quiescence semantics. Section 2.5 supplies the
provider-specific success requirement: exactly one candidate at signed ordinal
`0`; known failure declares an explicit empty tuple and zero total; the durable
delivery binds terminal plus companion. The companion is not a second CPN token
and does not alter 12/8 topology.

**Required next evidence:** later implementation and fixtures must map the exact
owner record fields and pass owner conformance vectors 33–41. No additional
design decision remains.

### U2 — immutable saved-state artifact-set identity

The current manifest authenticates files but the repository has no accepted
path-free immutable artifact-set identity/retention contract. A directory path
cannot fill that role.

**Recommendation:** the artifact owner returns an immutable collection identity
whose resolution is required to yield every and only manifest-declared files;
the provider candidate binds that identity and manifest reference. Do not use a
provider path or infer the collection from the manifest artifact alone.

### U3 — exact bounded cancellation capability (selected)

The version-one child export declares exactly:

```text
cancellation_input_ports = ()
definition_declared_cancellation_terminal_classifications = ()
in_net_cancellation_supported = false
runtime_cancellation_propagation = "unsupported-by-child-definition"
confirmed_not_applied_containment = true
confirmed_applied_result_processing = "required-through-existing-event-ports"
```

`CONFIRMED_NOT_APPLIED` is admitted only when Workflow evidence establishes that
no protected effect was applied, no child process remains, and no later attempt
was admitted. It operationally releases/contains the nested child; it does not
fabricate a CPN terminal token or fire the reserved parent scientific
transition.

`CONFIRMED_APPLIED` is not cancellation success. The exact observed result must
be processed through the existing `task_submitted`, `task_completed`,
`task_failed`, and/or `output_analyzed` event ports until the existing net
produces success or known failure. `STILL_AMBIGUOUS`, `EVIDENCE_INVALID`,
`CONFIRMED_PARTIAL`, a requested cancellation, timeout, lost lease, or worker
loss is nonterminal and cannot establish quiescence.

The existing `task_failed` arcs from `task_waiting` and `analysis_action` remain
ordinary known-failure routes; they are not reclassified as universal
cancellation. Linking must reject any parent/deployment policy that requires an
in-net cancellation input or definition-declared cancelled terminal outcome.
This declaration is exact and no longer an unresolved choice.

### U4 — canonical control-value bridge

Current SNAKES markings carry frozen domain records and one observation contains
binary64 scientific values; owner control JSON forbids implicit binary64. The
exact canonical product/reference representation and operation identities do
not yet exist.

**Recommendation:** keep guard facts as bounded canonical control fields, keep
the full observation as an immutable payload reference, and bind the exact
adapter/value model into the CPN execution profile. Golden parity must compare
transition traces and decoded domain outcomes, not Python object representation.

### U5 — current evidence is insufficient for production handoff

Current `CalculatorExecutionRecord` contains a working-directory string and is
not itself the path-free Workflow evidence chain requested here. Current SCF
handler does not build/retain a saved-state manifest or candidate.

**Recommendation:** retain the existing record as native evidence, add a
path-free content-addressed provider evidence projection correlated by Workflow,
and build the candidate only from that projection plus exact retained native
artifacts. Do not mutate old records to pretend the missing chain already
exists.

### U6 — identifiers and digests unavailable before implementation

Canonical IR, execution-profile, plan, export, artifact-set, codec implementation,
and golden fixture digests cannot be honestly predeclared.

**Recommendation:** leave them explicitly unavailable until separately
authorized implementation creates exact bytes; then independently verify them.
Do not use nominal text as a substitute.

Stop before implementation/linking if any selected U1–U5 contract lacks an exact
implementation/fixture, if parity changes the 12/8 behavior, if topology is copied, if a path
enters canonical evidence, or if authority/acceptance is inferred from the
candidate.

## 6. Actionable design review

### Finding 1

**Disposition: NO_ACTION_REQUIRED**
**Problem:** The provider design must bind exact corrected owner, primary
consumer, and saved-state-lineage successors without creating reciprocal
content-hash cycles.
**Evidence:** Section 0 binds owner Git `9ec0944dad3af1706edf01101e443e244da22ef5`
and SHA-256 `e6428a8b...`, plus consumer Git
`4ef67e49f11a00e66f5c6ed6f4f2d72eb441505a` and exact primary/lineage SHA-256
values `e3496191...` and `e49bb819...`. Those files were independently rehashed
and semantically checked before this focused commit. The consumer documents do
not embed this later provider digest.
**Consequence:** None at design level; no reciprocal future digest appears in a
core design document.
**Next action:** Bind the final provider commit/document identity with the exact
owner and consumer identities only in a later separate retained review record.

### Finding 2

**Disposition: MUST_FIX**
**Problem:** No current immutable artifact-set identity or complete path-free
Workflow-correlated success-evidence projection exists for this handoff.
**Evidence:** `QeSavedStateManifest` authenticates files, while the current
execution record carries a working-directory string and the SCF handler emits no
saved-state candidate.
**Consequence:** A candidate could depend on a mutable path or fail to prove that
the exact manifest-listed bytes came from the authorized successful attempt.
**Next action:** Implement U2 and U5 only after separate authorization, with the
fixture/tamper vectors above.

### Finding 3

**Disposition: MUST_FIX**
**Problem:** The deterministic canonical value/operation/export profile and
golden parity bytes do not yet exist.
**Evidence:** Current execution is the private SNAKES net; the Workflow contract
remains unimplemented and no canonical export digest is available. Section 3.4
now selects an exact version-pinned expression extraction and AST-lowering route
but does not implement it.
**Consequence:** The child cannot yet be linked or replayed as an exact canonical
Workflow plan.
**Next action:** Implement the closed exporter and golden fixtures in migration
phase 1 only after separate authorization; block payload binding and nesting
until parity passes.

### Finding 4

**Disposition: NO_ACTION_REQUIRED**
**Problem:** The unchanged 12/8 child cannot truthfully declare universal in-net
cancellation.
**Evidence:** U3 declares zero cancellation ports, zero cancellation terminal
classifications, no in-net cancellation, exact reconciliation containment, and
mandatory processing of confirmed-applied results through existing ports.
**Consequence:** None if linking enforces that exact declaration; unsupported
parent cancellation requirements fail closed.
**Next action:** None for design; preserve the declaration in later fixtures.

### Finding 5

**Disposition: NO_ACTION_REQUIRED**
**Problem:** A greenfield replacement or copied topology might appear necessary
to add saved-state delivery.
**Evidence:** The post-terminal handoff references the retained existing outcome,
and the exporter traverses the authoritative constructed factory through the
exact route in section 3.4; neither changes or duplicates the 12/8 CPN.
**Consequence:** None if the migration order and stop conditions are followed.
**Next action:** None.

### Finding 6

**Disposition: NO_ACTION_REQUIRED**
**Problem:** The earlier candidate proposal described values as bounded without
providing enough exact limits for a canonical validator.
**Evidence:** Section 2.3 fixes document size and depth, ASCII/control rules,
identity/text/safe-name lengths and grammars, integer/byte limits,
pseudopotential and manifest collection limits, path exclusions, and
lower/upper/out-of-bound fixture vectors.
**Consequence:** The version-one codec no longer needs implementation-local
limits if it follows this exact profile.
**Next action:** None for design; preserve these values byte-for-value in later
schema and fixtures.

### Finding 7

**Disposition: NO_ACTION_REQUIRED**
**Problem:** The existing terminal token and separately retained provider
candidate require an ordered two-input Si-VC terminal mapping without changing
the child net.
**Evidence:** The corrected owner successor semantics define classification-
specific delivery and companion requirements, canonical order, pre-mapper
admission, durable delivery, replay, ambiguity, and quiescence. Section 2.5 maps
the QE success candidate exactly, includes the child-export correlation, and
declares empty known-failure companions.
**Consequence:** None at design level; implementation still must pass the exact
owner companion vectors without hidden resolution or topology changes.
**Next action:** Preserve these semantics in later implementation fixtures.

**ReviewOutcome: CHANGES_REQUIRED**
Findings 2 and 3 must be resolved before a conforming nested implementation can
claim readiness. Findings 1 and 4–7 are resolved at design level only; they
provide no implementation evidence.

**OperatorRequest: NONE**
No implementation, protected execution, dependency change, commit, push,
release, publication, or acceptance is requested or authorized by this design
document.
