# Local SCF colored Petri-net implementation

## Authority and provenance

`cpn/net.py` is the authoritative executable SCF topology pending WORKFLOWS
extraction. It is byte-identical to
`examples/projectkoios/applications/pw_dft_scf/workflow/net.py` at Applications
commit `416be52d539bfbffdbc8a27bd8e13de65404821b`, Git blob
`7d6600ba8cbf0b079871d8c325b352bbf22d6afd`, with SHA-256
`4d580f686382851b32fccfbb7aa775782e3c44daf9e6efcf6d1cd95ca9d2d563`.

The detached `PwDftScfWorkflowDefinition` inventories the net name, place names,
and transition names. It does not duplicate or replace the arcs, guards, or
token expressions below. A conformance test requires those names to remain
identical.

## Places

`build_dft_pw_scf_net(evaluation_id)` constructs `PetriNet("dft_pw_scf")` with
twelve typed places:

| Place | Accepted token | Role and initial marking |
|---|---|---|
| `workflow_start` | `PwDftScfWorkflowStart` | Contains one initial token for `evaluation_id`; consumed when the workflow starts. |
| `request` | `PwDftScfRequestReference` | Contains one initial request reference; read through SNAKES `Test` arcs when terminal outcomes are constructed. |
| `registration_action` | `RegisterPwDftScfTask` | External registration action requested by the net. |
| `task_registered` | `PwDftScfTaskRegistered` | Boundary event reporting an allocated task ID. |
| `submission_action` | `SubmitPwDftScfTask` | External submission action requested after registration. |
| `task_submitted` | `PwDftScfTaskSubmitted` | Boundary event confirming external submission. |
| `task_waiting` | `PwDftScfTaskSubmitted` | Internal waiting-state token derived from the correlated submission event. |
| `task_completed` | `PwDftScfTaskCompleted` | Boundary event carrying the correlated output-artifact ID. |
| `task_failed` | `PwDftScfTaskFailed` | Boundary event accepted while waiting or analyzing. |
| `analysis_action` | `AnalyzePwDftScfOutput` | External normalization/analysis action requested after completion. |
| `output_analyzed` | `PwDftScfOutputAnalyzed` | Boundary event carrying one normalized observation. |
| `terminal_outcome` | `PwDftScfWorkflowOutcome` | Unique success or failure outcome produced by a terminal transition. |

All places enforce SNAKES `Instance` checks. Only `workflow_start` and `request`
are initially marked.

## Transitions, arcs, and guards

The net has eight transitions: one unguarded start transition and seven guarded
correlation or acceptance transitions.

| Transition | Input arcs | Guard | Output expression |
|---|---|---|---|
| `start_workflow` | consumes `workflow_start`; tests `request` | none | `RegisterPwDftScfTask(start.evaluation_id)` → `registration_action` |
| `accept_registration` | consumes `registration_action` and `task_registered` | action and event `evaluation_id` values are equal | `SubmitPwDftScfTask(registered.task_id)` → `submission_action` |
| `accept_submission` | consumes `submission_action` and `task_submitted` | action and event `task_id` values are equal | the submitted event → `task_waiting` |
| `accept_completion` | consumes `task_waiting` and `task_completed` | waiting and completion `task_id` values are equal | `AnalyzePwDftScfOutput(task_id, output_artifact_id)` → `analysis_action` |
| `accept_analysis` | consumes `analysis_action` and `output_analyzed`; tests `request` | task IDs match and the observation is both completed and converged | `PwDftScfWorkflowSucceeded(PwDftScfResult(...))` → `terminal_outcome` |
| `reject_analysis` | consumes `analysis_action` and `output_analyzed`; tests `request` | task IDs match and the observation is not both completed and converged | `PwDftScfWorkflowFailed` with code `scf-not-complete-and-converged` → `terminal_outcome` |
| `accept_analysis_failure` | consumes `analysis_action` and `task_failed`; tests `request` | action and failure `task_id` values are equal | failure with the event code and message → `terminal_outcome` |
| `accept_failure` | consumes `task_waiting` and `task_failed`; tests `request` | waiting and failure `task_id` values are equal | failure with the event code and message → `terminal_outcome` |

A `Test` input is a read arc: it preserves the request token. All other listed
inputs are consuming arcs. The net injects only the six reviewed constructors
used by its output expressions into `net.globals`; it does not call SNAKES
`declare()`, evaluate caller-provided code, load PNML, or unpickle a net.

## Facade event and action boundary

`LocalPwDftScfWorkflow.accept()` maps supported domain events to places as
follows:

| Event type | Boundary place |
|---|---|
| `PwDftScfTaskRegistered` | `task_registered` |
| `PwDftScfTaskSubmitted` | `task_submitted` |
| `PwDftScfTaskCompleted` | `task_completed` |
| `PwDftScfTaskFailed` | `task_failed` |
| `PwDftScfOutputAnalyzed` | `output_analyzed` |

Unsupported event types raise `TypeError`. A supported but currently
uncorrelated event does not fire a transition; its token remains in the private
local net and `accept()` returns an empty transition tuple. This bounded adapter
does not provide durable event routing, rejection delivery, deduplication, or
idempotency. Those remain WORKFLOWS runtime concerns.

`pending_actions()` returns detached tokens from `registration_action`,
`submission_action`, and `analysis_action`, in that order. It never invokes an
action or calculator.

## Bounded local firing

`LocalSnakesRun.drain_unique()` repeatedly fires only when exactly one transition
and one binding are enabled. It returns the fired transition names in order.
Zero enabled transitions means external input is required. Ambiguous transitions
or bindings raise `RuntimeError`. Reaching
`PwDftScfRuntimeConfiguration.maximum_internal_firings` also raises
`RuntimeError`; the positive bound is local loop protection, not a retry budget.

The mutable SNAKES net remains private. Token snapshots are detached and sorted
by `repr` for deterministic inspection.

## Status and outcome projection

`LocalPwDftScfWorkflow.status()` projects the private marking in this priority
order:

| Present token | Status |
|---|---|
| `terminal_outcome` | `terminated` |
| `analysis_action` | `analyzing` |
| `task_waiting` | `waiting-for-completion` |
| `submission_action` | `awaiting-submission` |
| `registration_action` | `awaiting-registration` |
| none of the above | `ready` |

`outcome()` returns `None` before termination and the sole
`PwDftScfWorkflowOutcome` afterward. More than one terminal token is treated as
an invariant violation and raises `RuntimeError`.

## Authority boundary

The package is wheel-carried but dependency-optional. The `cpn` extra supplies
the reviewed `projectkoios-snakes` source at commit
`c959528c3b35c12563b7ba291ca036e1ebb58f7e`. The distribution is named
`projectkoios-snakes` while preserving the compatible `snakes` import. The net consumes typed external
events and emits typed actions and outcomes. It contains no executable path,
provider implementation, queue, lease, retry service, persistence mechanism, or
calculator authority. Tests use synthetic events and never execute a
calculator.
