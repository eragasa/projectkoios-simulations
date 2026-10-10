# Runner configuration

`runner.toml` identifies the reviewed projection/recipe catalog, exact structure
catalog, and authenticated exact simulation catalog by bounded relative paths.
The simulation manifest byte size and SHA-256 are pinned before it is parsed.

Campaign files select a stable simulation ID from that authenticated catalog.
They no longer reconstruct structures, exchange-correlation intent, sampling,
electronic controls, or pseudopotential identities from tool-owned profile
fragments. `catalog.toml` retains only convergence coordinates and policies plus
QE and VASP calculator-input translation settings.

Operator-local executable, pseudopotential, workspace, and timeout paths remain
outside these source-controlled files. Loading a campaign, structure, or
simulation record does not authorize calculator execution.
