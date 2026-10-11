# QE SCF operation boundaries

## Status

The maintained implementation exposes two combined public operations:

- `QeScfInputProjector.project(...)` performs calculator-input translation and
  deterministic input rendering, returning an exact `CalculatorInputRecord`;
- `QeScfDataExtractor.extract(...)` loads bounded retained artifacts, parses
  native QE data, and normalizes the result into `QeScfData` and its
  calculator-neutral `PwDftScfObservation`.

Projection, rendering, parsing, and normalization are distinct architectural
responsibilities even when one maintained method currently performs more than
one of them. Separate public actionizers for all four stages are deferred. This
page defines their meanings; it does not claim that those future APIs exist or
choose their class names, dependencies, or namespaces.

## Vocabulary

### Calculator-input translation (legacy API name: projection)

Calculator-input translation maps calculator-neutral scientific intent into an
exact provider-native input description.

For QE SCF, its authoritative inputs are the `PwDftScfRequest`, the authenticated
`StructureResolution`, and explicit `QeScfProjectionConfiguration`. Conceptually,
translation produces a validated QE-native input description and explicit
neutral-to-native mappings. The maintained public method immediately renders
that description and returns one exact `CalculatorInputRecord` containing the
rendered artifacts, exact external requirements, mappings, and preparation
provenance.

The existing Python class is named `QeScfInputProjector`, but architecture prose
uses **calculator-input translation**. Here, “projection” does not mean a CPN
status view, an output-evidence projection, a mathematical projection operator,
or a selection of scientific acceptance policy.

Translation may:

- resolve already-supplied neutral fields into supported QE fields;
- reject intent that the supported QE input model cannot represent exactly;
- record exact pseudopotential and structure dependencies; and
- record the neutral-to-native meaning of every supported mapping.

Translation must not discover local files, select scientific intent, stage
artifacts, authorize execution, run `pw.x`, parse outputs, or accept a result.

### Input rendering

Input rendering deterministically serializes a validated provider-native input
model into exact calculator-input bytes, such as `pw.in`.

Rendering owns lexical details: QE namelist/card ordering, delimiters, numeric
formatting, units written to the file, filenames, and encoded bytes. Equal
validated inputs under the same rendering profile must produce equal bytes.
Changing any rendered byte changes the prepared-input artifact identity.

Rendering must not reinterpret neutral scientific intent, search for
pseudopotentials, write into an attempt directory, grant execution authority, or
start a process. In the maintained implementation rendering is an internal part
of `QeScfInputProjector.project(...)`; the returned `CalculatorInputRecord`
retains its result.

### Native-output parsing

Parsing decodes exact supplied QE-native bytes into provider-native records. For
SCF this includes bounded stdout and stderr parsing and, when supplied, QEXSD
interpretation.

Parsing owns syntax and native representation: token recognition, native field
names, native units, explicit optionality, schema/version checks, and bounded
malformed-input failure. It must preserve which exact artifact supplied each
fact.

Artifact lookup and file reading are not parsing. The current
`QeScfDataExtractor` performs bounded retained-artifact loading before invoking
parsers, but a future pure parser would consume bytes and artifact identities
supplied by a separate retention boundary. Parsing must not invent missing
values, treat `JOB DONE` as complete execution evidence, convert a native fact
into scientific acceptance, or authorize another action.

### Normalization

Complete normalization maps parsed provider-native records, together with exact
input and execution lineage, into calculator-neutral records. For QE SCF the
principal neutral result is `PwDftScfObservation`, retained inside `QeScfData`
with native sources and mechanical consistency observations. The maintained SCF
path retains its execution and native sources; complete correlation with the
exact `CalculatorInputRecord` remains required where the current evidence path
does not yet provide it.

Normalization owns explicit semantic adaptation, including unit conversion,
sign conventions, provider-to-neutral field meaning, unavailable-value handling,
and normalization provenance. For example, native QE energy in Ry is converted
to eV, while retained native artifacts remain available for audit.

Normalization must not alter retained native bytes, repair a failed execution,
choose convergence thresholds, declare provider candidacy, decide campaign or
scientific acceptance, grant staging authority, or authorize execution. A new
normalization of the same immutable source bytes is new derived evidence; it
does not replace its sources.

## Adjacent operations that remain separate

The four terms above do not include:

- **artifact resolution or staging** — locating, verifying, and copying exact
  files into one authorized attempt boundary;
- **calculator execution** — the separately authorized
  `CalculatorExecutor.action(...)` process attempt;
- **retention** — committing immutable input, output, manifest, or evidence
  bytes to their owning store;
- **Workflow correlation** — binding occurrences, plans, attempts, authority,
  history, and terminal delivery; or
- **qualification and acceptance** — provider candidacy, convergence policy,
  campaign acceptance, publication, or downstream scientific judgment.

No prepared input, parsed record, normalized observation, manifest, candidate,
or successful prior run grants authority for any adjacent operation.

## End-to-end flow

```text
neutral SCF request + authenticated structure + QE policy
    -> calculator-input translation (called projection by the current API)
    -> deterministic input rendering
    -> exact CalculatorInputRecord
    -> separately authorized staging and calculator execution
    -> immutable retained native bytes and execution evidence
    -> native-output parsing
    -> normalization with exact lineage
    -> neutral observation and evidence
    -> separately owned qualification or scientific acceptance
```

Every arrow preserves exact source identity. Replay may repeat translation,
rendering, parsing, or normalization over immutable supplied inputs without
implying that execution occurred again.

## Deferred decomposition

A future four-action decomposition is admissible only if it preserves the
current exact structure, pseudopotential, charge, spin, prepared-input,
execution, artifact, and evidence contracts. It must not introduce a parallel
production model, a compatibility facade, a namespace relocation, machine-path
content in portable records, or a dependency solely to recover an obsolete
prototype. Until such an implementation is separately reviewed, the combined
maintained methods above remain authoritative.
