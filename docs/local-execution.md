# Local execution deployment template

## Status

`local-execution.example.toml` is an **operator-only deployment template**. Copy
it to the ignored repository-root `local-execution.toml` when recording paths
for local manual use.

The repository currently provides no production parser, loader, schema object,
or automatic tool integration for this file. Its presence is not a supported
runtime API, and no workflow, test, example, or smoke marker reads it to obtain
execution authority. The template and its local copy do not constitute execution
authorization. A future loader requires separate design review, typed
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

| Key | Operator meaning | Current software behavior |
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

## Intended manual workflow

1. Copy `local-execution.example.toml` to `local-execution.toml`.
2. Replace every placeholder with a machine-local absolute path.
3. Keep the local file ignored and uncommitted.
4. Pass required paths explicitly to the relevant repository tool or domain
   object; no automatic loader exists.
5. Supply execution authorization separately if and only if a calculator runner
   is intentionally invoked.
