from __future__ import annotations

import numpy as np
from physkit.periodic import DirectLattice3D
from physkit.periodic.unit_cell import (
    Atom,
    AtomicBasis,
    UnitCell,
)
from physkit.units import PhysicalUnit, ScalarQuantity, Unitless, VectorQuantity

from projectkoios.simulations.dft.pw.relaxation.base import (
    PwDftRelaxationConvergencePolicy,
    PwDftRelaxationRequest,
    PwDftRelaxationSampling,
    PwDftRelaxationScope,
)
from projectkoios.simulations.dft.pw.settings import (
    CalculationType,
    PwDftSettings,
)
from projectkoios.simulations.dft.pw.simulation import PwDftSimulation


def silicon_relaxation_request(
    scope: PwDftRelaxationScope,
) -> PwDftRelaxationRequest:
    calculation = {
        PwDftRelaxationScope.ATOMIC_POSITIONS: CalculationType.relax,
        PwDftRelaxationScope.ATOMIC_POSITIONS_AND_CELL: CalculationType.vc_relax,
    }[scope]
    variable_cell = scope is PwDftRelaxationScope.ATOMIC_POSITIONS_AND_CELL
    return PwDftRelaxationRequest(
        evaluation_id="silicon-relaxation-test",
        simulation=PwDftSimulation(
            unit_cell=UnitCell(
                direct_lattice=DirectLattice3D(
                    a1=np.array([0.5, 0.5, 0.0]),
                    a2=np.array([0.0, 0.5, 0.5]),
                    a3=np.array([0.5, 0.0, 0.5]),
                ),
                lattice_parameter=ScalarQuantity(5.43, PhysicalUnit("angstrom")),
                atomic_basis=AtomicBasis(
                    atoms=(
                        _silicon_atom((0.0, 0.0, 0.0)),
                        _silicon_atom((0.25, 0.25, 0.25)),
                    )
                ),
            ),
            settings=PwDftSettings(calculation_type=calculation),
        ),
        scope=scope,
        sampling=PwDftRelaxationSampling(
            kpoint_mesh=(4, 4, 4),
            kpoint_shift=(0, 0, 0),
            wavefunction_cutoff_ev=300.0,
        ),
        convergence=PwDftRelaxationConvergencePolicy(
            maximum_ionic_steps=7,
            total_energy_tolerance_ev=0.001,
            force_tolerance_ev_per_angstrom=0.01,
            target_pressure_kbar=0.0 if variable_cell else None,
            pressure_tolerance_kbar=0.5 if variable_cell else None,
        ),
    )


def _silicon_atom(position: tuple[float, float, float]) -> Atom:
    return Atom(
        symbol="Si",
        position_fractional=VectorQuantity(np.array(position), Unitless()),
    )
