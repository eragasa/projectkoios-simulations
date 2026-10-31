# Wannier90 localization execution implementation

## Current API

`Wannier90LocalizationInputPreparer` authenticates and correlates the first closed
rank-reducing non-spin input profile. `Wannier90LocalizationRunner` consumes its exact
manifest and a separately authorized `Wannier90LocalizationRunRequest`.
`Wannier90LocalizationOutputVerifier` can reverify an already retained occurrence
without resolving or invoking a calculator. Immutable request, manifest,
preparation-result, run-result, and retained-output-error records are public from
`projectkoios.integrations.wannier90`.

This first implementation deliberately does not support non-disentangled, spin,
spinor, UNK-consuming, checkpoint-restart, or selective-localization profiles.

## Prepared occurrence

The implementation separates pure preparation from execution. Preparation validates
and correlates a closed route-specific native
input inventory, then creates exact prepared-input evidence without resolving
an executable or granting authority.

For the ordinary AMN/MMN localization route, preparation verifies exact
construction input, preprocessing topology, interface eigenvalues,
projections, neighbor overlaps, seedname, parent identity, dimensions, source
order, and spin convention. Converter-produced UNK wavefunctions remain a
correlated sibling inventory for a named downstream consumer or native
postprocessing mode; they are not included in ordinary localization prepared
input. Only a separately reviewed, explicitly supported native mode that
actually consumes UNKs may declare them as staged inputs. Otherwise the runner
rejects them as undeclared localization input rather than treating the route as
a permissive superset.

## Execution preflight

Before creating an occurrence output directory or starting a process, the provider
runner verifies:

- the complete prepared-input manifest and every staged artifact by size and
  SHA-256;
- safe, seed-consistent native basenames and unique physical inputs;
- exact parent, construction, preprocessing, and converter occurrence
  identities;
- route kind and required/optional role closure;
- exact executable path, mode, byte size, SHA-256, and declared version;
- positive finite timeout and declared operational bounds;
- a new nonsymlink output directory separate from every predecessor; and
- separately supplied external execution authorization.

A configured executable, environment variable, test marker, prior success, or
prepared-input record does not authorize execution.

## Single-attempt execution

The runner stages immutable input bytes and submits one no-shell command
to `projectkoios.simulations.execution`. It starts at most one subprocess,
provides no interactive stdin, and retains stdout and stderr independently. It
must not run preprocessing, invoke `pw2wannier90.x`, schedule another
occurrence, retry, or infer a restart.

Restart behavior is route-specific and explicit. The default is a fresh
occurrence. If a future reviewed route supports checkpoint restart, it must
bind exact checkpoint bytes and predecessor identity and produce a new
occurrence. It must never overwrite or mutate the source occurrence.

## Output inspection and failures

After process termination, the provider authenticates the declared native
output inventory before parsing. The accepted first generic non-spin spectral
profile requires `.wout` and `_hr.dat`; it requires `_u.mat` and `_u_dis.mat`
exactly when the declared construction needs the corresponding transformations.
It records process status separately from:

- presence and exact identity of required outputs;
- native completion markers;
- parsed localization convergence/status observations;
- dimensional and source-order correlation against the canonical WIN k-point block;
  and
- provider handoff completion.

Timeout, signal, nonzero exit, a missing or undeclared selected retained-output
role, symlink, changed bytes, parse failure, non-finite value, reported
nonconvergence, or dimensional mismatch produces retained evidence and no
successful provider handoff. The closed set governs the retained evidence
manifest, not every incidental file the native executable may create in its
private work directory. Incidental files are ignored or separately inventoried
and are never silently promoted to route evidence. A process can return zero
while the provider result remains failed or inconclusive.

NNKP writes reciprocal coordinates with lower native presentation precision than WIN
and the transformation-matrix files. The provider therefore uses WIN as the canonical
source-order reference for `u` and `u_dis`. It separately correlates NNKP to WIN under
the declared native serialization bound. It must not compare the more precise matrix
coordinates directly against lossy NNKP presentation bytes under a tighter tolerance.

Retained-output reverification authenticates the occurrence input manifest and staged
input bytes before applying the same output checks. It returns immutable JSON bytes and
never invokes, retries, or discovers a calculator.

## Dependency and adaptation boundaries

The production runner imports same-integration parser components and
protected calculator-input, execution, and artifact/evidence contracts. It
must not import `projectkoios.simulations.workflows`, downstream projects,
repository tools/examples, or live Workflow runtime objects.

The runner returns provider-native records. The ProjectKoios simulations
distribution must provide a separately reviewed first-party outward
`projectkoios.adapters` surface that maps authenticated observations to neutral
localization and representation roles. The adapter owns the mapping but not either underlying contract. This
preserves the asymmetric dependency rule: neither the inward workflow layer nor
the outward integration imports the other.

## Verification requirements

Tests use deterministic native fixtures and fake executables and must prove:

- exact closed AMN/MMN/EIG input inventories for ordinary localization;
- no global UNK requirement and no UNK staging into ordinary localization;
- sibling UNK correlation to a named downstream consumer, with localization
  staging allowed only for a separately reviewed native mode that consumes it;
- rejection of mixed parents, seednames, route kinds, roles, dimensions, and
  source orders before process startup;
- render/prepare-only behavior without executable discovery;
- fail-closed authorization and at most one subprocess;
- no shell, implicit restart, retry, or successor activation;
- refusal to overwrite or follow unsafe/symlinked paths;
- durable output for timeout, signal, nonzero exit, missing output, parse
  failure, reported nonconvergence, and dimension mismatch;
- exact authentication before native parsing;
- canonical WIN correlation despite lower-precision native NNKP serialization;
- no-calculator retained-output reverification without occurrence mutation;
- separation of process success from localization status and acceptance;
- absence of workflow imports from provider production modules; and
- no scientific calculator execution in ordinary checks.

Passing provider tests does not establish a scientifically adequate Wannier
representation.
