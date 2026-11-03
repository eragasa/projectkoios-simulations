# `pw.vc_relax.data_extraction`

`QeVcRelaxDataExtractor` extracts variable-cell native sources and returns the
unified [`QeRelaxData`](../../relaxation/data/index.md) facade with
`calculation == "vc-relax"`.

No mode-specific data alias is exposed; callers consume `QeRelaxData` directly.
