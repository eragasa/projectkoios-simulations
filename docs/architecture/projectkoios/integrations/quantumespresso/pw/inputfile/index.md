# `inputfile`

This package owns the single typed component vocabulary for Quantum ESPRESSO
`pw.x` input. `base` declares every recognized namelist and data card, including
explicit placeholders for unsupported components. `model` owns bounded loose
parsing, deterministic rendering, and the assembled input-file record.
Namelist-specific packages consume those components; they do not define
parallel card hierarchies.
