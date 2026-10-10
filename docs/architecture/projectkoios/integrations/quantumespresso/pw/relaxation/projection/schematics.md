# QE relaxation calculator-input translation schematics

## Translation flow

```mermaid
flowchart LR
    request[PwDftRelaxationRequest<br/>occurrence + exact specification]
    structure[StructureResolution<br/>exact starting geometry]
    config[QeRelaxationInputConfiguration<br/>QE-native controls]
    mode{Calculation mode}
    common[project_relaxation_input]
    checks{Fail-closed mapping checks}
    cards[Common QE cards]
    cell[Optional CELL card]
    input[Deterministic pw.in]

    request --> common
    structure --> common
    config --> common
    mode -->|relax| common
    mode -->|vc-relax + lattice options| common
    common --> checks
    checks -->|supported and compatible| cards --> input
    checks -->|unsupported or mismatched| reject[Reject translation]
    mode -->|vc-relax only| cell --> input
```

## Electronic-threshold qualification

```mermaid
flowchart LR
    neutral[Neutral energy_tolerance_ev]
    conversion[eV-to-Ry conversion]
    converted[Converted threshold in Ry]
    native[electronic_tolerance_ry]
    atol[electronic_atol_ry]
    compare{Absolute difference<br/>within atol?}
    electrons[QE ELECTRONS card<br/>conv_thr]
    reject[Reject translation]

    neutral --> conversion --> converted --> compare
    native --> compare
    atol -. comparison policy only .-> compare
    compare -->|yes| electrons
    compare -->|no| reject
    native --> electrons
```

`electronic_atol_ry` participates only in translation qualification. It is not
rendered into the QE input.

## Retained-declaration path

```mermaid
flowchart TD
    toml[Closed relaxation TOML]
    loader[QeRelaxationCalculationTomlLoader]
    declaration[QeRelaxationCalculationConfiguration]
    renderer[QeRelaxationCalculationRenderer]
    neutral[Neutral relaxation request]
    projection[relax or vc-relax projector]
    input[pw.in]

    toml --> loader --> declaration --> renderer
    renderer --> neutral --> projection --> input
    declaration -->|electronic_tolerance_ry| projection
    declaration -->|electronic_atol_ry| projection
```

## Authority and evidence boundary

```mermaid
flowchart LR
    translation[Relaxation input translation]
    prepared[Prepared QE input]
    authority[Separate explicit external authority]
    execution[pw.x execution]
    normalization[Output normalization]
    evidence[Simulation evidence]
    acceptance[Scientific acceptance]

    translation --> prepared
    prepared --> authority --> execution --> normalization --> evidence --> acceptance
    prepared --x execution
    prepared --x acceptance
```
