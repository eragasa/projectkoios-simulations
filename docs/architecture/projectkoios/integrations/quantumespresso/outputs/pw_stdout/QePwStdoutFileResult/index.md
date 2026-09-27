# `QePwStdoutFileResult`

Parsed stdout result with these native observations:

- `output_file`
- `program_version`
- `job_completed`
- `scf_converged`
- `total_energy_ry`
- `wavefunction_cutoff_ry`
- `pressure_kbar`
- `total_force_ry_per_bohr`
- `total_scf_correction_ry_per_bohr`
- `maximum_atomic_force_ry_per_bohr`
- `maximum_force_component_ry_per_bohr`
- `stress_ry_per_bohr_cubed`
- `geometry_optimization_converged`
- `bfgs_scf_cycle_count`
- `bfgs_step_count`
- `bfgs_energy_threshold_ry`
- `bfgs_force_threshold_ry_per_bohr`
- `bfgs_cell_threshold_kbar`
- `optimizer_total_force_ry_per_bohr`
- `optimizer_maximum_atomic_force_ry_per_bohr`
- `optimizer_maximum_force_component_ry_per_bohr`
- `optimizer_pressure_kbar`
- `optimizer_stress_ry_per_bohr_cubed`
- `bfgs_objective_kind`
- `previous_bfgs_objective_ry`
- `final_bfgs_objective_ry`
- `bfgs_energy_change_ry`
- `final_enthalpy_ry`
- `final_energy_ry`
- `scf_nonconvergence_count`
- `left_handed_axis_warning`
- `atom_count`
- `k_point_count`
- `scf_iteration_count`

The unqualified force, maximum atomic-force norm, maximum force component,
pressure, and stress fields represent the last values in the captured output. The `optimizer_*` values snapshot the observations present
when QE reports BFGS convergence, before a possible final-cell SCF prints
additional values. Native BFGS threshold values are retained for comparison to
the committed declaration. Matching `energy new`/`Final energy` or
`enthalpy new`/`Final enthalpy` observations provide the final BFGS objective
change without conflating fixed-cell energy with variable-cell enthalpy. `left_handed_axis_warning` records QE's warning
without converting it into an integration-generated failure. None of these
observations independently establishes workflow success.
