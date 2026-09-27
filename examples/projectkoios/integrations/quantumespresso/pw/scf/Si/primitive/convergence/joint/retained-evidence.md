# Retained bulk-silicon QE SCF evidence

This directory retains a complete 36-calculation `actual1` Quantum ESPRESSO
artifact grid as inert provider evidence. It contains native input,
standard-output, standard-error, and execution records and does not include a
campaign controller, convergence assessor, replay policy, or calculator runner.

## Evidence identity

`evidence/manifest.json` conforms to the closed `evidence/schema.json` contract
and identifies:

- the exact retained structure record;
- the declared QE 7.5 executable hash, size, and source revision;
- the declared Si UPF hash, size, and scientific metadata;
- the historical policy values recorded with the evidence;
- all 30 initial-grid and 6 adaptive-extension coordinates;
- every retained artifact's SHA-256 identity and byte size; and
- the structured IEEE warnings recorded from the calculations.

The executable and pseudopotential bytes are identified but are not copied into
this repository. Native calculation artifacts are retained under
`evidence/artifacts/`. `RetainedQeScfEvidenceLoader` verifies the closed manifest
and every repository-retained byte identity without interpreting convergence or
invoking Quantum ESPRESSO. The repository test suite exercises that integrity
check.

## Boundary

The removed application replay depended on the unmigrated
`projectkoios.frankensteins.applications.pw_dft_scf` owner boundary. This
integration does not reproduce its convergence assessment, extension decision,
or acceptance outcome.

These artifacts are historical finite-grid total-energy observations. Their
provenance and byte integrity do not establish current policy acceptance,
numerical verification, force or stress convergence, band or NSCF convergence,
or scientific validation.
