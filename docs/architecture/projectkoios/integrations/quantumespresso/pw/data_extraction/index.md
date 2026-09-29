# Shared `pw.x` data sources

`QePwDataSources` composes parsed captured streams, optional parsed QEXSD data,
optional execution evidence, and an optional exact execution-artifact identity.
It is shared by the SCF, NSCF, `relax`, and `vc-relax` facades.

Composition keeps stdout, stderr, QEXSD, execution records, and artifact
identities distinct. Construction validates execution/stream filename pairing
but does not merge observations or decide scientific acceptance. Mode facades
add mode-specific normalized data and mechanical consistency observations while
retaining compatibility properties for the previous flattened access paths.
