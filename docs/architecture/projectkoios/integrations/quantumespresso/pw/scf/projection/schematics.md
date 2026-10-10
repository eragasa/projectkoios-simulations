# QE SCF calculator-input translation schematics

## Translation flow

```mermaid
flowchart LR
    request[PwDftScfRequest<br/>occurrence + exact specification]
    structure[StructureResolution<br/>exact record + verified UnitCell]
    config[QeScfProjectionConfiguration<br/>species + QE-native controls]
    projector[QeScfInputProjector]
    checks{Fail-closed mapping checks}
    input[Deterministic pw.in]
    requirements[External UPF basenames]

    request --> projector
    structure --> projector
    config --> projector
    projector --> checks
    checks -->|supported and exact| input
    checks -->|supported and exact| requirements
    checks -->|unsupported or mismatched| reject[Reject translation]
```

## Electronic-threshold boundary

```mermaid
flowchart LR
    neutral[Neutral energy_tolerance_ev]
    conversion[eV-to-Ry conversion]
    converted[Converted neutral threshold in Ry]
    native[electronic_tolerance_ry]
    atol[electronic_atol_ry]
    compare{Absolute difference<br/>within atol?}
    convthr[pw.in conv_thr]
    reject[Reject translation]

    neutral --> conversion --> converted --> compare
    native --> compare
    atol -. comparison policy only .-> compare
    compare -->|yes| convthr
    compare -->|no| reject
    native --> convthr
```

Only `electronic_tolerance_ry` supplies the rendered `conv_thr` value.
`electronic_atol_ry` participates in qualification but has no edge to a native
calculator setting.

## Authority boundary

```mermaid
flowchart LR
    projector[QeScfInputProjector]
    prepared[Prepared QE input]
    authority[Separate explicit external authority]
    execution[pw.x execution]
    evidence[Execution evidence]
    acceptance[Scientific acceptance policy]

    projector --> prepared
    prepared --> authority --> execution --> evidence --> acceptance
    prepared --x execution
    prepared --x acceptance
```
