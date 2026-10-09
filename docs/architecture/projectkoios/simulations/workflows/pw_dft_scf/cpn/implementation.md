# Local SCF colored Petri-net implementation

`net.py` is the byte-identical Applications source from
`examples/projectkoios/applications/pw_dft_scf/workflow/net.py` at commit
`416be52d539bfbffdbc8a27bd8e13de65404821b`, blob
`7d6600ba8cbf0b079871d8c325b352bbf22d6afd`, and remains the authoritative SCF
topology pending WORKFLOWS extraction. Its SHA-256 is
`4d580f686382851b32fccfbb7aa775782e3c44daf9e6efcf6d1cd95ca9d2d563`.
It creates twelve typed places and
seven guarded transitions, including their input/output arcs and token
expressions, using reviewed domain constructors. It injects only named
constructors into net globals and does not use SNAKES `declare()`, arbitrary
`exec`, PNML, or pickle.

`runtime.py` keeps the mutable net private, returns detached token snapshots,
and fires only when exactly one transition and binding are enabled. A positive
configured firing bound prevents an accidental internal loop.

`workflow.py` maps typed SCF events to boundary places, projects private
markings into `PwDftScfWorkflowStatus`, and exposes at most one terminal outcome.
The maintained `projectkoios-snakes` fork at commit
`72dbb1dbf0a91349faca21ceb660923cc442a8e9` supplies the `snakes` namespace.

The package is wheel-carried but dependency-optional. The `cpn` extra supplies
the immutable reviewed SNAKES source. A direct conformance test proves that the
detached workflow definition matches the net's name, places, and transitions;
the definition does not duplicate its arcs or guards. Other direct tests use
synthetic domain events and perform no calculator execution.
