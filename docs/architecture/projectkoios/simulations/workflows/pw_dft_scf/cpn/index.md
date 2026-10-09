# Local SCF colored Petri net

`projectkoios.simulations.workflows.pw_dft_scf.cpn` is the executable local
SNAKES binding for one calculator-neutral SCF lifecycle. It was transferred
from Applications with the workflow capability so a future WORKFLOWS extraction
can move the complete engine adapter rather than reconstruct it from an example.

The package constructs a typed `snakes.nets.PetriNet`, wraps bounded unique
firing, and implements `PwDftScfWorkflowFacade`. It owns no calculator
executable, queue, durable scheduler state, or reusable authority.

SNAKES is optional. Importing the general simulation or workflow packages does
not import this CPN package; callers install the `cpn` extra when selecting this
local engine.
