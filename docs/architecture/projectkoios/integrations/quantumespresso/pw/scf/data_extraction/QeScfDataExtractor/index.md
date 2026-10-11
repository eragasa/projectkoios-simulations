# `QeScfDataExtractor`

Fields: `artifact_root` and `maximum_artifact_bytes`.

`extract(output_artifact_id, qexsd_document=...)` verifies successful execution
evidence and returns `QeScfData`. QEXSD remains optional because historical SCF
evidence may retain only stdout, stderr, and `execution.json`.

The extractor owns bounded filesystem loading only. It delegates supplied bytes
to `QeScfOutputParser.action(...)` and delegates the resulting provider records
and exact execution lineage to `QeScfNormalizer.action(...)`. It does not carry a
second parsing or normalization implementation.
