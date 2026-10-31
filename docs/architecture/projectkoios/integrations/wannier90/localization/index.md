# Wannier90 localization execution integration

## Status

`localization_execution.py` implements the first rank-reducing, ordinary non-spin
AMN/MMN provider profile. `Wannier90LocalizationInputPreparer` creates and correlates
a closed WIN/NNKP/EIG/AMN/MMN inventory without resolving an executable.
`Wannier90LocalizationRunner` verifies that manifest, the exact executable identity,
resource bounds, and explicit authorization before submitting at most one process to
the generic single-attempt executor. `Wannier90LocalizationOutputVerifier` applies the
same authenticated provider checks to an existing occurrence without invoking a
calculator.

The existing `localization.py` remains the execution-independent `.wout` parser. The
runner does not grant execution authority, discover executables, retry, restart, or
accept a scientific Wannier representation.

## Purpose

The capability owns one provider-native localization occurrence. It:

1. consumes exact preprocessing and converter identities plus a route-specific
   authenticated interface artifact set;
2. stages one closed, seed-consistent native input inventory;
3. verifies the exact `wannier90.x` executable and occurrence resources;
4. submits at most one separately authorized localization process through the
   generic single-attempt executor;
5. retains exact process and native output evidence; and
6. parses supported localization, gauge, disentanglement, and real-space
   Hamiltonian outputs into provider observations; and
7. supports no-calculator reverification of retained outputs against the canonical WIN
   reciprocal-point order.

The runner must separate process completion, native-reported localization
status, output-set closure, parser success, route correlation, and scientific
acceptance.

## Route-specific input closure

The ordinary AMN/MMN localization route requires exact construction input,
preprocessing topology identity, interface eigenvalues, projections, and
neighbor overlaps. It does not require or consume UNK wavefunction files.
Converter-produced UNKs are correlated sibling evidence for a named downstream
wavefunction consumer or native postprocessing mode, not ordinary localization
inputs. They may be staged into a localization occurrence only if a separately
reviewed, explicitly supported native mode declares that it consumes them; no
such mode is implied by this architecture.

Optional spin, operator, checkpoint, restart, or postprocessing artifacts are
also route-qualified. A closed localization input inventory identifies every
required and permitted role. Unknown extras—including UNKs when no supported
native mode consumes them—missing required roles, changed bytes, or mixed
parents fail before execution.

## Ownership boundary

The outward integration owns native staging, seedname/basename rules,
localization command projection, exact native output manifests, provider
parsing, and provider-level correlation. It does not own:

- scientific selection of projections, windows, rank, thresholds, restart
  policy, or requested observables;
- the neutral `pw_dft_wannierization` route or its scientific acceptance;
- QE NSCF or `pw2wannier90.x` execution;
- queues, retries, leases, cancellation, or workflow-runtime state;
- executable discovery or reusable execution authority; or
- downstream interpolation, effective-mass, operator, or publication policy.

The integration must not import `projectkoios.simulations.workflows`. A
first-party outward `projectkoios.adapters` surface must map authenticated
provider observations to neutral roles using public contracts from both owners.

## Output evidence

A successful provider result identifies exact input and execution records plus
a route-qualified output inventory. The accepted first generic non-spin
spectral profile requires the primary `.wout` and real-space Hamiltonian. It
also requires gauge and disentanglement matrices exactly when the declared
construction needs those transformations; checkpoints and other outputs remain
explicitly profile-qualified. Centers, spreads, and iteration summaries are
parsed observations from
the authenticated `.wout`; they are not standalone artifacts. Any separately
requested native center-output file is an additional explicitly declared
artifact with its own identity and parser contract. Absence and presence are
both explicit; no output is accepted by basename alone.

Gauge and disentanglement k-points are compared with the canonical WIN k-point block,
not the lower-precision NNKP presentation. NNKP is separately correlated to WIN under
the native serialization bound. This prevents a formatting-only precision difference
from being misclassified as source-order disagreement.

A completed localization produces a candidate provider representation. It does
not prove convergence, interpolation accuracy, operator fidelity, or
scientific acceptance.

See [`implementation.md`](implementation.md) for the planned execution and
failure rules, [`schematics.md`](schematics.md) for artifact and authority
flows, [`scientific.md`](scientific.md) for interpretation limits, and
[`numeric.md`](numeric.md) for cross-artifact dimensions and ordering.
