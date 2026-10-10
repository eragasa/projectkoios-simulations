from __future__ import annotations

from projectkoios.simulations.dft.electronic import (
    DftOccupationMethod,
    DftOccupationPolicy,
    PwDftElectronicConvergencePolicy,
)
from projectkoios.simulations.dft.pw.scf.specification import PwDftScfSpecification
from projectkoios.simulations.dft.pw.settings import PwDftKPointSamplingPolicy
from projectkoios.simulations.dft.pw.simulation import PwDftSimulation
from tests.projectkoios.simulations.dft.pw.support import (
    pbe_exchange_correlation,
    silicon_structure_resolution,
)


def silicon_scf_specification() -> PwDftScfSpecification:
    structure = silicon_structure_resolution()
    return PwDftScfSpecification(
        simulation_id="Si.PrimitiveUnitCell.QE.SCF",
        simulation=PwDftSimulation(
            structure=structure.record,
            exchange_correlation=pbe_exchange_correlation(),
        ),
        kpoint_sampling=PwDftKPointSamplingPolicy(
            mesh=(8, 8, 8),
            shift=(0, 0, 0),
            use_spatial_symmetry=True,
            use_time_reversal=True,
        ),
        wavefunction_cutoff_ev=400.0,
        occupation=DftOccupationPolicy(method=DftOccupationMethod.FIXED),
        electronic_convergence=PwDftElectronicConvergencePolicy(
            energy_tolerance_ev=1.3605693122994e-5,
            maximum_electronic_iterations=100,
        ),
    )
