# Examples

This directory contains several kinds of material with different contracts. Start
with the category matching the task; retained evidence and source snapshots are not
runnable tutorials.

## Runnable, execution-free demonstrations

| Demonstration | Purpose | Calculator execution |
|---|---|---|
| [`authenticate_qe_wannier90_provider.py`](authenticate_qe_wannier90_provider.py) | Authenticate and correlate caller-supplied retained QE and Wannier90 artifacts. | Never |
| [`parse_wannier90_native_artifacts.py`](parse_wannier90_native_artifacts.py) | Parse a caller-supplied directory of native Wannier90 artifacts. | Never |
| [`workflows/pw_dft_relaxation/qe_projection.py`](workflows/pw_dft_relaxation/qe_projection.py) | Project calculator-neutral relaxation intent into QE-native input. | Never |
| [`workflows/pw_dft_scf/replay_normalized_evidence.py`](workflows/pw_dft_scf/replay_normalized_evidence.py) | Replay normalized SCF evidence through workflow policies. | Never |

## Workflow declarations

[`workflows/`](workflows/README.md) contains compact, calculator-free examples of
simulation-domain composition:

- `pw_dft_scf/campaigns/`: four QE and four VASP campaign declarations;
- `pw_dft_scf/comparisons/`: four cross-provider comparison declarations;
- `pw_dft_scf/structures/`: maintained silicon structure documents; and
- `pw_dft_relaxation/`: a small relaxation projection demonstration.

These files describe workflow intent. They do not grant calculator authority.

## Package-owned reference material

[`projectkoios/`](projectkoios/README.md) follows package ownership:

- [`projectkoios/simulations/`](projectkoios/simulations/README.md) contains
  calculator-neutral structures and reciprocal-path documents;
- [`projectkoios/integrations/quantumespresso/`](projectkoios/integrations/quantumespresso/README.md)
  contains QE-native inputs, retained observations, and exact upstream example
  snapshots; and
- [`projectkoios/integrations/vasp/`](projectkoios/integrations/vasp/README.md)
  contains VASP-native inputs and retained observations.

Provider-native retained observations are evidence records, not tutorials. Passing a
parser or replay check does not establish convergence, scientific validity, or
permission to rerun the originating calculation.

## Local deployment

Machine-local executable paths and the pseudopotential-library root belong in the
repository-level `local-execution.toml`, copied from
[`../local-execution.example.toml`](../local-execution.example.toml). They do not
belong inside an individual retained example directory.
