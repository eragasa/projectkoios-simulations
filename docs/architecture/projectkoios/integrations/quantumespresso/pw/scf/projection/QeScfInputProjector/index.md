# QeScfInputProjector

`configuration` holds explicit QE-native policy. `project` consumes an exact
`StructureResolution`, validates supported neutral intent, and renders `pw.in`.
`_ev_to_ry` performs the maintained unit conversion.

The converted neutral electronic threshold must agree with
`configuration.electronic_tolerance_ry` within the absolute Ry-valued
`configuration.electronic_atol_ry`. Only `electronic_tolerance_ry` is rendered
as `conv_thr`; the comparison tolerance is not calculator input.
