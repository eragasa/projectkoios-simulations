# Local SCF colored Petri-net implementation

`net.py` creates twelve typed places and seven guarded transitions using
reviewed domain constructors. It injects only named constructors into net
globals and does not use SNAKES `declare()`, arbitrary `exec`, PNML, or pickle.

`runtime.py` keeps the mutable net private, returns detached token snapshots,
and fires only when exactly one transition and binding are enabled. A positive
configured firing bound prevents an accidental internal loop.

`workflow.py` maps typed SCF events to boundary places, projects private
markings into `PwDftScfWorkflowStatus`, and exposes at most one terminal outcome.
The maintained `projectkoios-snakes` fork at commit
`72dbb1dbf0a91349faca21ceb660923cc442a8e9` supplies the `snakes` namespace.

The package is wheel-carried but dependency-optional. The `cpn` extra supplies
the immutable reviewed SNAKES source. Direct tests use synthetic domain events
and perform no calculator execution.
