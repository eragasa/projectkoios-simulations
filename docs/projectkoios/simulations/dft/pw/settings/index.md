# `projectkoios.simulations.dft.pw.settings`

Calculator-neutral plane-wave DFT settings and the machine-readable QE/VASP projection registry. `CalculationType` defines shared calculation modes. `AlignmentKind` classifies projection fidelity. `PwDftTag` identifies semantic settings, and `TagAlignment` records their calculator fields and qualifications. A `PwDftSimulation` owns one `PwDftSettings`; calculator adapters read those settings rather than asking callers to repeat equivalent calculator fields.

`PW_DFT_TAG_ALIGNMENT_REGISTRY` contains one `TagAlignment` for every `PwDftTag`. Each entry names its QE and VASP fields, classifies each projection, and states its qualification. Registry membership does not itself authorize a lossy projection: conditional, approximate, and unsupported mappings must remain visible in adapter results.
