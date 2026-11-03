# `QeVcRelaxDataExtractor`

The constructor requires exact stdout and stderr artifact paths. `extract(...)`
owns variable-cell relaxation extraction and returns the unified
[`QeRelaxData`](../../../relaxation/data/index.md) facade with
`calculation == "vc-relax"`.
