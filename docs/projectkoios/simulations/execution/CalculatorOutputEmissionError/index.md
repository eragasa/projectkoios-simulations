# `CalculatorOutputEmissionError`

Operational error raised when native output was retained but could not be emitted
to the corresponding parent binary console stream. The attached
`CalculatorExecutionRecord` and `record_path` describe the calculator process's
actual terminal status; console availability does not reclassify that process
attempt or change native artifact identity.
