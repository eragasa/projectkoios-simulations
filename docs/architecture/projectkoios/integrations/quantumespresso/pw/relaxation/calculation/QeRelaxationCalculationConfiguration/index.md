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
`electronic_tolerance_ry`, `maximum_ionic_steps`,
`total_energy_tolerance_ry`, `force_tolerance_ry_per_bohr`,
`target_pressure_kbar`, `pressure_tolerance_kbar`, `prefix`, `pseudo_dir`,
`outdir`, `input_filename`, `coordinate_precision`, `ion_dynamics`,
`cell_dynamics`, `cell_degrees_of_freedom`, and `qualification_statements`.

Fixed-cell `relax` forbids cell controls. `vc-relax` requires pressure, cell
dynamics, and cell-degree-of-freedom declarations.
