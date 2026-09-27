# `QeNscfDataExtractor`

`extract(stdout_payload, stderr_payload, qexsd_document,
expected_band_count, expected_kpoint_count, ...)` binds exact streams to parsed
QEXSD spectral data and fails closed when declared dimensions disagree. Raw XML
is rejected so semantic XML parsing remains owned by `ksdft2effmass`.
