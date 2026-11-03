# `QeNscfDataExtractor`

The constructor requires expected band and k-point counts plus exact stdout and
stderr artifact paths. `extract(stdout_payload, stderr_payload, qexsd_document,
...)` binds those streams to parsed QEXSD spectral data and fails closed when
declared dimensions disagree. Raw XML is rejected so mechanical XML parsing
remains owned by `projectkoios.integrations.quantumespresso.qexsd`.
