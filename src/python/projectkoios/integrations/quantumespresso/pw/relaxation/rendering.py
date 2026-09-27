"""Render validated Quantum ESPRESSO relaxation calculations."""

from __future__ import annotations

from dataclasses import dataclass

from physkit.periodic.unit_cell import UnitCell
from physkit.units import MODEL_SYSTEM_UNIT_CONVERTER, PhysicalUnit

from projectkoios.integrations.quantumespresso.pw.inputfile.base import (
    QeAtomicSpecies,
)
from projectkoios.integrations.quantumespresso.pw.relax.configuration import (  # noqa: E501
    QeRelaxProjectionConfiguration,
)
from projectkoios.integrations.quantumespresso.pw.relax.projection import (  # noqa: E501
    QeRelaxInputProjector,
)
from projectkoios.integrations.quantumespresso.pw.vc_relax.configuration import (  # noqa: E501
    QeVcRelaxProjectionConfiguration,
)
from projectkoios.integrations.quantumespresso.pw.vc_relax.projection import (  # noqa: E501
    QeVcRelaxInputProjector,
)
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

from .calculation import QeRelaxationCalculationConfiguration


@dataclass(frozen=True, slots=True)
class QeRelaxationCalculationRenderer:
    """Project a calculation configuration and unit cell into deterministic input."""

    def render(
        self,
        configuration: QeRelaxationCalculationConfiguration,
        unit_cell: UnitCell,
    ) -> str:
        """Return one phase-specific Quantum ESPRESSO input document."""
        if type(configuration) is not QeRelaxationCalculationConfiguration:
            raise TypeError(
                "configuration must be a QeRelaxationCalculationConfiguration"
            )
        if not isinstance(unit_cell, UnitCell):
            raise TypeError("unit_cell must be a UnitCell")
        phase = configuration.phase
        scope = {
            "relax": PwDftRelaxationScope.ATOMIC_POSITIONS,
            "vc-relax": PwDftRelaxationScope.ATOMIC_POSITIONS_AND_CELL,
        }[phase]
        calculation_type = {
            "relax": CalculationType.relax,
            "vc-relax": CalculationType.vc_relax,
        }[phase]
        request = PwDftRelaxationRequest(
            evaluation_id=f"{configuration.calculation_id}-{phase}",
            simulation=PwDftSimulation(
                unit_cell=unit_cell,
                settings=PwDftSettings(calculation_type=calculation_type),
            ),
            scope=scope,
            sampling=PwDftRelaxationSampling(
                kpoint_mesh=configuration.kpoint_mesh,
                kpoint_shift=configuration.kpoint_shift,
                wavefunction_cutoff_ev=_convert(
                    configuration.wavefunction_cutoff_ry,
                    "Ry",
                    "eV",
                ),
            ),
            convergence=PwDftRelaxationConvergencePolicy(
                maximum_ionic_steps=configuration.maximum_ionic_steps,
                total_energy_tolerance_ev=_convert(
                    configuration.total_energy_tolerance_ry,
                    "Ry",
                    "eV",
                ),
                force_tolerance_ev_per_angstrom=_convert(
                    configuration.force_tolerance_ry_per_bohr,
                    "Ry/bohr",
                    "eV/angstrom",
                ),
                target_pressure_kbar=configuration.target_pressure_kbar,
                pressure_tolerance_kbar=configuration.pressure_tolerance_kbar,
            ),
        )
        species = (
            QeAtomicSpecies(
                symbol=configuration.pseudopotential_symbol,
                mass_amu=configuration.pseudopotential_mass_amu,
                pseudopotential_filename=configuration.pseudopotential_filename,
            ),
        )
        ratio = (
            configuration.charge_density_cutoff_ry
            / configuration.wavefunction_cutoff_ry
        )
        if phase == "relax":
            projection = QeRelaxInputProjector(
                QeRelaxProjectionConfiguration(
                    species=species,
                    ion_dynamics=configuration.ion_dynamics,
                    charge_density_cutoff_ratio=ratio,
                    electronic_tolerance_ry=configuration.electronic_tolerance_ry,
                    prefix=configuration.prefix,
                    pseudo_dir=configuration.pseudo_dir,
                    outdir=configuration.outdir,
                    input_filename=configuration.input_filename,
                    coordinate_precision=configuration.coordinate_precision,
                )
            ).project(request)
        else:
            assert configuration.cell_dynamics is not None
            assert configuration.cell_degrees_of_freedom is not None
            projection = QeVcRelaxInputProjector(
                QeVcRelaxProjectionConfiguration(
                    species=species,
                    ion_dynamics=configuration.ion_dynamics,
                    charge_density_cutoff_ratio=ratio,
                    electronic_tolerance_ry=configuration.electronic_tolerance_ry,
                    prefix=configuration.prefix,
                    pseudo_dir=configuration.pseudo_dir,
                    outdir=configuration.outdir,
                    input_filename=configuration.input_filename,
                    coordinate_precision=configuration.coordinate_precision,
                    cell_dynamics=configuration.cell_dynamics,
                    cell_degrees_of_freedom=configuration.cell_degrees_of_freedom,
                )
            ).project(request)
        return projection.rendered_inputs[0].text


def _convert(value: float, source: str, target: str) -> float:
    return value * MODEL_SYSTEM_UNIT_CONVERTER.conversion_factor(
        PhysicalUnit(source),
        PhysicalUnit(target),
    )
