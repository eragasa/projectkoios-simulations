# `QePw2Wannier90ArtifactInspector`

Fields `max_artifact_count`, `max_total_byte_size`, and
`max_eigenvalue_byte_size` bound inspection.
`inspect(output_directory, seedname, producer_execution_record_sha256, declarations)` verifies every declared
regular file's size and SHA-256. It requires one `.amn`, `.mmn`, and `.eig`,
checks AMN/MMN dimensions agree, and requires a complete finite EIG
band-by-k-point grid. It records native dimensions but makes no Wannier-quality
decision. The observation retains exact producer execution-record correlation.
