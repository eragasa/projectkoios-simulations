# `QeSavedStateManifestVerifier`

Fields `max_artifact_count` and `max_total_byte_size` bound inspection.
`verify(manifest, source_root)` checks every selected artifact's regular-file
status, size, SHA-256, parent directories, and stable file identity in manifest
order. Symbolic links, concurrent changes, and identity mismatches fail closed.
