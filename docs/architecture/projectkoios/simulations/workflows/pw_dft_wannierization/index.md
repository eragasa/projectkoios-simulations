# Plane-wave DFT Wannierization workflow capability

## Status

This node specifies a planned owner-specific workflow capability. The production
`projectkoios.simulations.workflows.pw_dft_wannierization` package, public
records, workflow definition, and executable topology do not yet exist. This
documentation does not add an API, compose a provider, start a calculator, or
grant execution authority.

The current repository contains reusable prerequisites, including neutral
simulation and execution records, Quantum ESPRESSO SCF and NSCF components,
`pw2wannier90.x` integration components, and execution-independent Wannier90
artifact parsers. Those prerequisites do not constitute the planned end-to-end
workflow. In particular, the current
`projectkoios.integrations.wannier90` architecture is parser-only and expressly
owns no subprocess behavior. Preprocessing and localization runners require a
separate reviewed outward-integration change before this workflow can consume
normalized observations from them.

The planned route also requires an exact parent structure/numerical-setting pair
from the planned
[`pw_dft_bulk_qualification`](../pw_dft_bulk_qualification/index.md) capability.
That predecessor is unimplemented. Its documentation does not qualify a
structure or add hidden calculations to this route.

## Purpose

After bulk qualification has accepted one exact structure/setting pair, the
planned capability will represent the provider-neutral scientific composition
that connects:

1. a qualified plane-wave DFT parent state;
2. a source-ordered uniform-grid Bloch-frame requirement;
3. a localization-preprocessing requirement;
4. a plane-wave-to-localization interface requirement;
5. a localization requirement; and
6. exact representation evidence suitable for separately owned comparison and
   acceptance policies.

The route contains five calculator occurrences: parent SCF, uniform-grid NSCF,
Wannier90 preprocessing, `pw2wannier90.x` interface generation, and Wannier90
localization. Bulk qualification is a separate predecessor campaign and may
have many SCF/relaxation occurrences; it is not a sixth hidden route occurrence.
Each required calculator calculation is one simulation occurrence. The
composition may describe predecessor requirements, non-authorizing handoffs,
artifact roles, and typed outcomes. It must not select Quantum ESPRESSO or
Wannier90, encode their native input syntax, discover executables, carry an
authorization token, schedule occurrences, retry failures, or decide a
consumer's scientific acceptance thresholds.

## Ownership boundary

| Concern | Authoritative owner | Boundary |
| --- | --- | --- |
| Bulk structure/settings qualification and feedback | Planned `projectkoios.simulations.workflows.pw_dft_bulk_qualification` | Required predecessor; unimplemented and outside the five-occurrence route |
| Neutral route requirements, lineage, decisions, and handoff semantics | `projectkoios.simulations.workflows.pw_dft_wannierization` | Planned; no production package exists |
| Exact neutral specifications, prepared inputs, one-attempt execution records, and evidence references | Protected `projectkoios.simulations` core | Existing generic contracts remain authoritative |
| Quantum ESPRESSO SCF, NSCF, QEXSD, saved-state, and `pw2wannier90.x` native behavior | `projectkoios.integrations.quantumespresso` | Outward provider implementation; no workflow-policy ownership |
| Wannier90 native parsing | `projectkoios.integrations.wannier90` | Existing execution-independent capability |
| Future Wannier90 preprocessing and localization execution | `projectkoios.integrations.wannier90` after separate architecture and implementation review | Planned prerequisite; not a current surface |
| Provider/native-to-neutral mapping | Planned outward `projectkoios.adapters` surface | Required distribution capability; imports public contracts from both layers without reversing their dependencies |
| Provider selection, operational configuration, and route invocation | Planned `tools/pw_dft_wannierization` | Required repository capability; must not enter this workflow package |
| Queues, leases, retries, cancellation, occurrence admission, and durable scheduling | External Workflow runtime | Not owned by this repository capability |
| Material choices, windows, projections, thresholds, promotion, and retained calculation results | Consuming scientific project | Values are validated, not selected, here |

The planned package points inward only to protected-core contracts and public
sibling workflow contracts, including the accepted bulk qualification handoff.
It never imports `projectkoios.integrations` or a
live Workflow runtime. Outward composition may adapt provider-native records to
neutral handoffs, but that dependency direction does not allow native provider
objects to leak into the workflow contract.

## Artifact profiles

Artifact-role closure is profile-specific. The accepted first generic non-spin
spectral profile closes through NNKP, EIG/AMN/MMN, required WOUT and real-space
Hamiltonian roles, and unitary/disentanglement matrices exactly when required by
the declared construction. It does not require parent wavefunctions. A
component-operator extension additionally declares and closes
the exact parent-wavefunction evidence roles its consumer requires. Native
plane-wave coefficients and provider-native real-space samples such as UNK are
distinct representations; one must not be relabeled as the other without an
explicit, verified transform and complete conventions. UNK is not a neutral
globally mandatory role. The consuming scientific campaign chooses the profile;
this workflow validates the roles that profile declares.

## Planned route outcomes

The route must distinguish requirements, mechanical completion, normalized
evidence, and scientific disposition. Candidate outcome concepts include:

- parent-state evidence available or required;
- uniform-grid frame evidence available or required;
- preprocessing handoff available or rejected;
- interface handoff available or rejected;
- localization observation available, failed, or inconclusive; and
- representation evidence available for downstream assessment.

Names remain provisional until implementation review. An “available” outcome
means only that the declared identity and consistency checks succeeded. It does
not mean that a subprocess is authorized, localization converged, interpolation
is accurate, or a representation is scientifically accepted.

## Topology status

This architecture is not an executable Petri net or a complete canonical plan.
It does not define queues, places, transitions, arcs, guards, token
expressions, retry semantics, or runtime occurrence identity. If a workflow
shape is later needed, it must be complete enough to avoid competing with the
current authoritative SCF Petri net or with a future generic Workflow compiler.
Until then, implementation should begin with immutable requirements, handoffs,
correlation results, and decisions rather than a second partial topology.

See [`implementation.md`](implementation.md) for the planned package and import
rules, [`schematics.md`](schematics.md) for dependency and authority flows,
[`scientific.md`](scientific.md) for the provider-neutral scientific meaning,
[`numeric.md`](numeric.md) for identity, ordering, and dimensional consistency
requirements, and
the consolidated
[Tranche 1 review](../../../../../pw-dft-wannierization-review.md) for the reuse
inventory, minimal route delta, compatibility treatment, and remaining decisions.
