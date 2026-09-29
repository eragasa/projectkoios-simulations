# `pw.nscf.data_extraction`

NSCF-owned data facade and extraction:

- `QeNscfData`
- `QeNscfSpectralData`
- `QeNscfConsistency`
- `QeNscfDataExtractor`

The extractor consumes the maintained parser's immutable QEXSD document rather
than parsing XML itself. The facade retains that supplied document record and
interpreted final structure while composing source-ordered spectral data and
captured native streams.
