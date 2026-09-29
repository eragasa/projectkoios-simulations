# `pw.relax.data_extraction`

`QeRelaxDataExtractor` extracts fixed-cell native sources and returns the
unified [`QeRelaxData`](../../relaxation/data/index.md) facade with
`calculation == "relax"`.

The extractor does not decide scientific acceptance and does not treat
configuration or output content as calculator-execution authorization.
