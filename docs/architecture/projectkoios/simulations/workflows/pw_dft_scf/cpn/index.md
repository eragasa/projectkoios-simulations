# Local SCF colored Petri net

`projectkoios.simulations.workflows.pw_dft_scf.cpn` is the executable local
SNAKES binding for one calculator-neutral SCF lifecycle. It was transferred
from Applications with the workflow capability so a future WORKFLOWS extraction
can move the complete engine adapter rather than reconstruct it from an example.

The package's `build_dft_pw_scf_net()` constructs the authoritative typed
`snakes.nets.PetriNet`. That code defines the complete executable topology:
places, transitions, input/output arcs, guards, and token expressions. The
package also wraps bounded unique firing and implements
`PwDftScfWorkflowFacade`. It owns no calculator executable, queue, durable
scheduler state, or reusable authority.

SNAKES is optional. Importing the general simulation or workflow packages does
not import this CPN package; callers install the `cpn` extra when selecting this
local engine.

The source-conformance gate binds `cpn/net.py` to its reviewed byte size and
SHA-256, constructs the net through SNAKES, and verifies that topology, color
checks, guards, annotations, and evaluator globals are independent of the
evaluation identity. Only the two initial typed tokens vary between evaluation
instances. This gate intentionally emits no private canonical Workflow format:
the future exporter must consume this constructed SNAKES net through the stable
Workflow owner API.

See [`implementation.md`](implementation.md) for the normative twelve-place,
eight-transition topology, event correlation, bounded firing, status projection,
and authority contracts. See [`schematics.md`](schematics.md) for the compact
flow view.
