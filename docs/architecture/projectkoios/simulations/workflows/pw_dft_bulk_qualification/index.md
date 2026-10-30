# Plane-wave DFT bulk qualification workflow capability

## Status

This node specifies a planned provider-neutral workflow capability. The
production `projectkoios.simulations.workflows.pw_dft_bulk_qualification`
package, public records, adapters, repository tool, and executable topology do
not yet exist. The names in this documentation describe architectural roles;
they do not reserve Python APIs or establish compatibility obligations before a
separate implementation review.

This documentation does not execute a calculator, grant execution authority,
select a provider, or establish that any material is numerically or
scientifically qualified.

## Purpose

The planned capability will qualify one exact bulk structure and one exact
plane-wave numerical setting as a correlated pair before a downstream
production route consumes them. It composes three reusable stages:

1. a joint plane-wave-cutoff and reciprocal-sampling study on an exact seed
   structure `S0`, producing only a provisional qualification `Q0@S0`;
2. structural relaxation and zero-pressure qualification under that provisional
   setting, producing a mechanically qualified exact structure `S1`; and
3. a fresh final-setting confirmation on `S1`, producing `Q1@S1`.

If confirmation changes the required setting, the workflow does not transfer
qualification from `S0` or silently accept `S1` under the new setting. It
requests a new relaxation under `Q1`, obtains a new exact structure, and
confirms again. The bounded feedback continues until one structure/setting pair
is stable under the declared policy or the workflow reports failure,
inconclusive evidence, or budget exhaustion.

## Ownership boundary

| Concern | Authoritative owner | Boundary |
| --- | --- | --- |
| Exact calculator-neutral SCF and relaxation specifications, results, evidence references, structure records, pseudopotential requirements, and neutral plane-wave cutoff realization | Protected `projectkoios.simulations` core | Reuse existing contracts; add only the neutral cutoff record without changing current specification schemas |
| SCF recipes, joint grid assessment, controller decisions, and typed structure/evidence correlation | `projectkoios.simulations.workflows.pw_dft_scf` | Reuse existing convergence behavior; add correlation around its observations and assessment for `Q0` and `Q1` |
| Relaxation composition and zero-pressure structure assessment | `projectkoios.simulations.workflows.pw_dft_relaxation` | Reuse existing composition; add only pure zero-pressure assessment over its result |
| Cross-stage dependency, feedback, exact lineage, and stable-pair decision | Planned `projectkoios.simulations.workflows.pw_dft_bulk_qualification` | Required reusable composition; unimplemented |
| Provider-native SCF and relaxation behavior | Outward provider integrations | No workflow-policy ownership |
| Provider/native-to-neutral mapping | Planned first-party `projectkoios.adapters` surface | Required distribution capability; imports public contracts from both layers |
| Provider selection, operational configuration, pseudopotential source/catalog discovery and authorized acquisition, and route invocation | Planned outward integrations/adapters and `tools/pw_dft_bulk_qualification` | Preserve existing neutral pseudopotential records/resolver; no workflow network authority |
| Admission, queues, leases, retries, cancellation, and durable persistence | External Workflow runtime | One separately authorized occurrence at a time |
| Material choice, thresholds, cell mode, promotion, and scientific acceptance | Consuming scientific project | Values are validated, not selected, here |

The planned workflow package imports only protected-core and public sibling
workflow contracts. It never imports provider integrations, adapters,
repository tools, a consuming project, or a live Workflow runtime.

## Exact qualification scope

A numerical qualification is valid only for the exact structure and scientific
model recorded by its declaration. It binds at least the structure identity,
pseudopotential identities, exchange-correlation model, occupations, spin and
symmetry policy, the existing wavefunction-cutoff/grid coordinate, one neutral
wavefunction and density/potential cutoff realization, tested observations,
assessment policy, and typed child request/input/occurrence/evidence
correlation. The current convergence assessment alone is not structure-scoped.

A mechanically qualified structure is likewise bound to the exact numerical
setting used for its relaxation. Provider completion or an optimizer convergence
marker is not by itself zero-pressure acceptance. The reusable assessment keeps
process completion, normalized force and pressure facts, allowed cell changes,
mechanical consistency, workflow disposition, and scientific acceptance
separate.

## Relationship to Wannierization

The planned
[`pw_dft_wannierization`](../pw_dft_wannierization/index.md) capability consumes
a parent state descended from an accepted bulk structure/setting pair. Bulk
qualification is a predecessor campaign and may require many separately
admitted SCF and relaxation occurrences. It does not become an extra hidden
stage inside the later five-occurrence SCF, NSCF, Wannier90 preprocessing,
`pw2wannier90.x`, and Wannier90 localization route.

The final-confirmation SCF occurrence does not serve as the later parent in this
architecture. Only after the exact structure/setting pair is accepted does the
composition emit a new parent-SCF requirement, preserving the downstream route
as five separately admitted occurrences. Any future occurrence-reuse proposal
would require separate scientific, role-closure, topology, and authority review;
matching energies, filenames, or friendly identifiers are insufficient.

See [`implementation.md`](implementation.md) for planned package and dependency
rules, [`schematics.md`](schematics.md) for feedback and authority flows,
[`scientific.md`](scientific.md) for interpretation limits,
[`numeric.md`](numeric.md) for exact identity and decision semantics, and
the consolidated
[Tranche 1 review](../../../../../pw-dft-wannierization-review.md) for the
reuse inventory, minimal gaps, compatibility treatment, and remaining decisions.
