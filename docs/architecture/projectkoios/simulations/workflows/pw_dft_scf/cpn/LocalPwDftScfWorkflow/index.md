# `LocalPwDftScfWorkflow`

`LocalPwDftScfWorkflow` implements `PwDftScfWorkflowFacade` with a private local
SNAKES colored Petri net. Construction creates one evaluation net and advances
to its first external action.

The facade exposes pending calculator-neutral actions, accepts supported typed
events, projects a coarse status, and returns the unique terminal outcome. It
does not perform the requested actions itself; provider execution and authority
remain outside the net.
