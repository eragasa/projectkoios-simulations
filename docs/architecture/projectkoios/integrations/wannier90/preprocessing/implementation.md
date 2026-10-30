# Planned Wannier90 preprocessing implementation rules

## No current API

This document defines implementation constraints, not public symbol names or
signatures. No source module, request type, result type, projector, runner, or
codec is created by this architecture-only change. A future API review must
select names and package shape without implying compatibility with provisional
document terminology.

The existing Wannier90 parser modules remain execution-independent. They are
not relocated, re-exported, or converted into runner facades by this plan.

## Separation of rendering and execution

The first renderer subset is reusable generic non-spin spectral Wannier90 input,
not a silicon-specific profile. A consuming project supplies every exact
structure, projection, energy window, k-point mesh, rank, and localization
control. The future implementation must provide a pure render-or-bind phase
that can:

- validate that complete provider-native construction input;
- deterministically render exact `.win` bytes or authenticate caller-supplied
  exact bytes;
- report required native resources and expected outputs; and
- construct a prepared-input record without resolving or running an executable.

A separate execution phase may stage the prepared input and submit one process
only after external authorization has been supplied at the existing
single-attempt execution boundary. Render-only behavior must reject execution
resources rather than retain dormant executable paths or authorization flags.
Configuration files, examples, environment variables, test markers, and the
presence of `wannier90.x` never grant authority.

## Preflight and side-effect order

Before creating an output directory or starting a process, the future provider
implementation must verify:

- a safe seedname and exact native input basename;
- the complete prepared-input byte size and SHA-256;
- exact structure, lattice, reciprocal-point order, projection, window, rank,
  spin, and predecessor identities carried by the construction declaration;
- an absolute nonsymlink executable path, executable mode, byte size, SHA-256,
  and declared version when execution is requested;
- a new nonoverlapping output directory;
- positive finite timeout and declared resource bounds; and
- absence of placeholders, unsafe path components, duplicate physical inputs,
  or undeclared resources.

After preflight, staging writes immutable input bytes into the new occurrence
directory. The runner submits exactly one no-shell command equivalent in meaning
to `wannier90.x -pp <seedname>` through
`projectkoios.simulations.execution`. It does not loop, retry, launch a child
route, or activate `pw2wannier90.x`.

## Evidence and failure behavior

The provider occurrence retains the exact input, stdout, stderr, terminal
execution record, and every declared compact output. The native neighbor file
is authenticated by size and digest before semantic parsing. Process success,
native completion observations, parse success, and provider handoff completion
remain distinct statuses.

A timeout, signal, nonzero return code, missing output, output symlink, changed
artifact, parse failure, or semantic inconsistency produces explicit retained
failure evidence. Partial outputs remain evidence but are not relabeled as a
successful topology handoff. A retry is a new occurrence and must not overwrite
the failed directory.

## Dependency direction and neutral adaptation

A future production preprocessing module may import:

- the Python standard library;
- existing Wannier90-native parsers in the same outward integration;
- protected calculator-input, execution, and artifact/evidence contracts; and
- explicitly reviewed low-level dependencies already allowed by the
  distribution.

It must not import `projectkoios.simulations.workflows`, a consuming
application, repository tools or examples, or a live Workflow runtime. It emits
provider-native records. The ProjectKoios simulations distribution must provide
a separately reviewed first-party outward `projectkoios.adapters` surface that
reads those records and constructs neutral role observations through public
contracts from both layers. This keeps both forbidden dependency arrows absent: workflows
do not import integrations, and integrations do not import workflows.

## Verification requirements

Implementation tests must use deterministic native fixtures and fake
executables. They must establish:

- deterministic byte-exact rendering or exact caller-input authentication;
- render-only operation without executable discovery or process startup;
- rejection of execution resources in render-only mode;
- rejection of missing external authorization before process startup;
- at most one subprocess and no implicit retry;
- exact command arguments without a shell or interactive stdin;
- preflight failure before output-directory creation where practical;
- refusal to overwrite or follow symlinked input/output paths;
- durable timeout, nonzero-exit, missing-output, and parser-failure evidence;
- exact neighbor-artifact authentication and source-order preservation;
- no import from `projectkoios.simulations.workflows`; and
- no scientific calculator execution during ordinary repository checks.

Passing these tests would establish software behavior only. It would not
qualify a scientific construction or prove compatibility with a particular
Wannier90 deployment.
