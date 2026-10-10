# Local execution deployment template

## Status

`local-execution.example.toml` is an **operator-only deployment template**. Copy
it to the ignored repository-root `local-execution.toml` when recording paths
for local manual use.

The repository provides no production parser, loader, schema object, or
automatic tool integration for this file. Its presence is not a supported
runtime API, and no workflow, test, example, or smoke marker reads it to obtain
execution authority. The template and its local copy do not constitute execution
authorization. Adding a loader requires separate design review, typed
validation, and explicit authorization semantics.

## Template fields

```toml
schema_version = 1

[executables]
pw = "/absolute/path/to/quantum-espresso/bin/pw.x"
pw2wannier90 = "/absolute/path/to/quantum-espresso/bin/pw2wannier90.x"
wannier90 = "/absolute/path/to/wannier90.x"

[pseudopotentials]
directory = "/absolute/path/to/quantum-espresso-pseudopotentials"
```

| Key | Operator meaning | Software behavior |
|---|---|---|
| `schema_version` | Documents template shape version `1`. | Not parsed or negotiated. |
| `executables.pw` | Intended local `pw.x` path. | Not discovered, validated, or invoked. |
| `executables.pw2wannier90` | Intended local `pw2wannier90.x` path. | Not discovered, validated, or invoked. |
| `executables.wannier90` | Intended local `wannier90.x` path. | Not discovered, validated, or invoked. |
| `pseudopotentials.directory` | Intended root supplied explicitly to `PseudopotentialLibrary`. | Not loaded automatically. |

Use absolute paths to avoid dependence on a caller's working directory. The
tracked example contains placeholders only. The ignored local copy may contain
machine-specific paths and must not be committed.

## Scientific and execution boundaries

The pseudopotential directory does not select a pseudopotential. Scientific code
must still provide a complete `PseudopotentialFile` with explicit metadata,
filename, byte size, and SHA-256. `PseudopotentialLibrary` only resolves those
already-selected exact bytes beneath a root explicitly supplied by the caller.

An executable path is deployment information, not reusable permission.
Calculator execution remains fail-closed and requires a separate explicit
authorization at the execution boundary. Copying, editing, rendering, or testing
this template grants no authority and executes no calculator.

## Manual workflow

1. Copy `local-execution.example.toml` to `local-execution.toml`.
2. Replace every placeholder with a machine-local absolute path.
3. Keep the local file ignored and uncommitted.
4. Pass required paths explicitly to the relevant repository tool or domain
   object; no automatic loader exists.
5. Supply execution authorization separately if and only if a calculator runner
   is intentionally invoked.

## Pytest simulation policy

`@pytest.mark.simulation` identifies a test that launches a real calculator.
Input rendering, retained-evidence parsing, contract tests, and fake-executable
tests do not carry this marker.

The marker classifies the test but grants no execution authority. Repository
pytest configuration skips every `simulation` test unless the operator supplies
the separate authorization option. Selecting the marker without that option
remains fail-closed.

```bash
# Selection alone: collected simulation tests remain skipped.
.venv/bin/python -m pytest -m simulation

# Explicitly authorized real-calculator test invocation.
.venv/bin/python -m pytest -m simulation \
  --authorize-calculator-execution
```

A marked test must receive calculator paths and exact external resources through
an explicit test or operator configuration. The authorization option does not
discover executables, select pseudopotentials, accept scientific results, or
turn `local-execution.toml` into a runtime API. Calculator processes must not be
started during test-module import or collection, before the authorization gate
can skip the test.

## QE Si/Ni spin validation

The marked QE spin-validation tests require two explicit environment variables:

- `PROJECTKOIOS_VALIDATION_QE_PW_EXECUTABLE`: absolute path to the exact QE 7.5
  `pw.x` declared by SHA-256 and byte size in the test;
- `PROJECTKOIOS_VALIDATION_QE_PSEUDOPOTENTIAL_LIBRARY`: absolute root injected
  into `PseudopotentialLibrary`.

The tests author complete Si and Ni `PseudopotentialFile` requirements. The
library resolves and verifies those exact bytes during each execution workflow;
it does not select an artifact by element or filename. The invocation remains
separately authorization-gated:

```bash
PROJECTKOIOS_VALIDATION_QE_PW_EXECUTABLE=/absolute/path/to/pw.x \
PROJECTKOIOS_VALIDATION_QE_PSEUDOPOTENTIAL_LIBRARY=/absolute/library/root \
.venv/bin/python -m pytest \
  tests/projectkoios/integrations/quantumespresso/pw/scf/validation \
  --authorize-calculator-execution
```

The Si case is an unpolarized spin-symmetric control. The Ni case uses the exact
retained `materials-project.mp-23.primitive` structure, Gaussian smearing, and a
2 μB authored symmetry-breaking initial moment. It accepts completed and
converged execution with nonzero total and absolute magnetization. This bounded
qualitative check does not establish numerical convergence or a reference Ni
magnetic moment.
