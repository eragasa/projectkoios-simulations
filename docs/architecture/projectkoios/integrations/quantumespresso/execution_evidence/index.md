# Quantum ESPRESSO execution-evidence boundary

This boundary qualifies how the 101 reusable-provider owners identified in the
KSD Quantum ESPRESSO ownership audit relate to maintained Project Koios
Simulations APIs. The machine-readable inventory is
[`crosswalk.json`](crosswalk.json).

The source inventory is the 2026-11-03 KSD audit at commit
`aa4098b3d32fe05436a1ba8dab18903a4347b20d`: 38 owners from `contracts.py`, 5
from `diagnostics.py`, 32 from `effects.py`, 17 from `execution.py`, 1 from
`outcomes.py`, 6 from `process.py`, and 2 from `pw_input.py`.

The earlier `UPSTREAM_DUPLICATE` classification means that the scientific
consumer and Simulations overlap at the capability level. It does **not** mean
that every KSD class can be replaced by one current Simulations class. In
particular, KSD records frequently combine calculator observations with
Workflow identities, artifact publication, persistence wire identities, and
scientific interpretation. Those concerns remain consumer-owned.

## Qualified result

| Capability | KSD owners | Disposition |
|---|---:|---|
| Native input and rendering | 10 | Partial upstream owner |
| Executable binding and preparation | 26 | Partial upstream owner |
| Process capture | 14 | Partial upstream owner |
| Diagnostic classification | 14 | Partial upstream owner |
| Workspace and native-output evidence | 20 | Missing reusable upstream owner |
| Terminal and calculator outcome | 14 | Partial upstream owner |
| Provider data and consumer result correlation | 3 | KSD adapter required |
| **Total** | **101** | Fully inventoried |

Simulations already owns exact rendered input files, external file
requirements, no-shell process requests, durable basic execution records,
bounded QE stdout/stderr parsing, native QEXSD parsing, and SCF, NSCF, and
bands data extraction. These APIs are nominally independent of KSD.

The current execution record is intentionally narrower than KSD's retained
operation evidence. It does not yet represent exact executable bytes,
allowlisted environment additions, stream content identities, monotonic wall
duration, explicit signal/timeout values, bounded workspace snapshots, a
general native-output manifest, or diagnostic-aware calculator outcomes.
Deleting the corresponding KSD owners before those gaps are either implemented
or assigned to the KSD adapter would lose evidence semantics.

## Required reusable tranches

1. Define exact executable identity and bounded local preparation without
   importing Workflow identities or execution authority from a consumer.
2. Define general bounded before/after workspace snapshots and native-output
   manifests. Publication remains the consuming Workflow's responsibility.
3. Define version-bound byte-span QE diagnostics and calculator-outcome
   resolution independently of retry or scientific acceptance policy.
4. Correlate process and terminal evidence with exact stream identities while
   preserving the existing basic execution-record wire until a separate schema
   decision is reviewed.

No implementation is copied from KSD in this qualification tranche. The
crosswalk prevents false equivalence and identifies the reusable gaps that must
be designed separately. No Quantum ESPRESSO process was invoked, and the audit
establishes no numerical or scientific validation.
