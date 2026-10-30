# Plane-wave DFT Wannierization workflow implementation rules

## Reuse-first package

The neutral production package does not yet exist. It will compose existing SCF,
QE NSCF, QE `pw2wannier90`, generic evidence, and Wannier90 parser capability.
Proposed module and symbol names remain unreserved.

Begin with only two persisted neutral concepts:

- one route requirement binding the accepted bulk stable pair, scientific
  construction, closed artifact profile, and ordered five-occurrence
  dependency; and
- one route result referencing exactly five selected evidence records and the
  normalized lineage/dimensional facts produced by adapters.

Add stage-specific neutral records only if implementation proves that these two
cannot enforce exact lineage and role closure.

## Dependencies

Neutral production modules may import only the standard library, protected
simulation contracts, and provider-independent sibling workflows. They must not
import integrations, adapters, tools, consuming applications, executable
configuration, or Workflow runtime implementations.

The route requirement/result contains no provider object, filename suffix,
local path, executable, authorization flag, queue state, lease, or retry state.
Generic `EvidenceArtifactReference` values carry neutral role, byte size, and
SHA-256; no second generic artifact-reference hierarchy is needed.

## Existing outward capability

Reuse unchanged:

- existing SCF workflow and evidence for the new parent occurrence;
- existing QE NSCF configuration, execution, saved state, and frame extraction;
- existing QE `pw2wannier90.x` configuration, runner, streams, and EIG/AMN/MMN
  inspection;
- existing Wannier90 artifact authentication and NNKP, EIG, AMN, MMN, `.wout`,
  unitary, disentanglement, and Hamiltonian parsers; and
- existing `CalculatorExecutor` for one authorized process.

The missing outward additions are only:

1. immutable native `.win` configuration and deterministic rendering for a
   reusable generic non-spin spectral subset; consuming projects supply all
   material-specific structures, projections, windows, meshes, and controls;
2. a thin `wannier90.x -pp seed` preprocessing wrapper over
   `CalculatorExecutor`; and
3. a thin `wannier90.x seed` localization wrapper over
   `CalculatorExecutor`.

The wrappers own native staging, command lines, streams, and artifact
authentication. They implement no Wannier90 algorithm or scientific decision.

## Route and role closure

After accepted bulk qualification, the five separately authorized occurrences
are:

1. new parent SCF;
2. uniform-grid NSCF;
3. Wannier90 preprocessing;
4. existing `pw2wannier90.x` conversion; and
5. Wannier90 localization.

The first ordinary route closes exactly one NNKP from preprocessing, exactly one
EIG/AMN/MMN from conversion, and exactly one WOUT and one real-space Hamiltonian
from localization. It also requires the unitary matrix and the disentanglement
matrix exactly when the declared construction needs each one. Closed roles
describe selected retained evidence; incidental native
work-directory files are ignored or separately inventoried rather than promoted
as route evidence. UNK, SPN, and component-operator roles are absent.

First-party `projectkoios.adapters` maps existing provider records to these
neutral roles and retains exact source/target identities. Provider integrations
do not import the neutral workflow. `tools/pw_dft_wannierization` owns provider
selection, operational configuration, resource resolution, authorization
requests, invocation, and replay. External Workflow infrastructure owns
scheduling and persistence.

## Existing specialized manifest

`QeWannier90PlaneWaveArtifactManifest` remains unchanged as a specialized
UNK/downstream-artifact aggregate. The ordinary route uses existing
`QePw2Wannier90ArtifactObservation`. No migration, deprecation, widening, or
replacement manifest is required.

## Verification

Calculator-free tests must establish:

- exact accepted bulk predecessor and parent lineage;
- exact `.win` rendering, staging, and command lines;
- executable, input, output, stream, and execution-record identity;
- five separate occurrence authorizations and selected retry identity;
- exact NNKP, EIG/AMN/MMN, required WOUT/HR, and construction-conditional
  U/U_dis role closure;
- existing parser dimension and source-order correlation;
- ordinary no-UNK/no-SPN behavior;
- separation of process, artifact, parser, provider, and neutral outcomes;
- unchanged existing provider/parser APIs and tests; and
- absence of provider imports or reusable authority in neutral modules.

Passing these tests establishes software consistency only, not localization
quality, interpolation accuracy, or scientific validation.
