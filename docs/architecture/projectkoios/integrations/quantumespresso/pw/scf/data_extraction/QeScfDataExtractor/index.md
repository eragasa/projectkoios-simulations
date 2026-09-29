# `QeScfDataExtractor`

Fields: `artifact_root` and `maximum_artifact_bytes`.

`extract(output_artifact_id, qexsd_document=...)` verifies successful execution
evidence and returns `QeScfData`. QEXSD remains optional because historical SCF
evidence may retain only stdout, stderr, and `execution.json`.
