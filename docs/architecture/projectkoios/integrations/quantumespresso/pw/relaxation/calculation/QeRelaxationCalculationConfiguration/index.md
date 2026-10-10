# `QeRelaxationCalculationConfiguration`

The cutoff condition is

$$
E_{\rho}\ge E_{\mathrm{wfc}}>0.
$$

The immutable declaration exposes `calculation_id`, `phase`, `integration_id`,
`energy_convergence_tolerance_mev_per_atom`, `structure`, `calculator`,
`calculator_program`, `calculator_version`, `calculator_source_revision`,
`pseudopotential`, `pseudopotential_symbol`, `pseudopotential_filename`,
`pseudopotential_exchange_correlation`, `pseudopotential_formalism`,
`pseudopotential_relativistic_treatment`, `pseudopotential_upf_version`,
`pseudopotential_mass_amu`, `kpoint_mesh`, `kpoint_shift`,
`wavefunction_cutoff_ry`, `charge_density_cutoff_ry`,
`electronic_tolerance_ry`, `electronic_atol_ry`, `ionic_relaxation`,
`lattice_vector_relaxation`, `prefix`, `pseudo_dir`, `outdir`,
`input_filename`, `coordinate_precision`, and `qualification_statements`.

`electronic_tolerance_ry` is the QE-native `conv_thr` value.
`electronic_atol_ry` is the finite, nonnegative absolute tolerance in Ry used
only to qualify conversion from the neutral eV threshold. The two fields are
not interchangeable.

`ionic_relaxation` is always a `QeIonicRelaxationOptions` record. Fixed-cell
`relax` requires `lattice_vector_relaxation` to be absent. `vc-relax` requires
it to be a `QeLatticeVectorRelaxationOptions` record.
