"""Project calculator-neutral SCF intent through maintained VASP writers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from projectkoios.integrations.vasp.calculation import (
    VaspCalculationProjector,
)
from projectkoios.integrations.vasp.incar import (
    IncarAssignment,
    IncarFile,
    IncarWriter,
)
from projectkoios.integrations.vasp.kpoints import (
    VaspAutomaticKpointMesh,
    VaspKpointsWriter,
)
from projectkoios.integrations.vasp.poscar import (
    PoscarModel,
    PoscarWriter,
    UnitCellModel,
)
from projectkoios.integrations.vasp.pw_dft_scf.configuration import (
    VaspScfProjectionConfiguration,
)
from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.calculator_input import (
    CalculatorExternalInputRequirement,
    CalculatorInputArtifact,
    CalculatorInputMapping,
    CalculatorInputRecord,
)
from projectkoios.simulations.dft.electronic import DftOccupationMethod, DftSpinMode
from projectkoios.simulations.dft.pseudopotential import (
    PseudopotentialArtifactFormat,
)
from projectkoios.simulations.dft.pw.scf.request import PwDftScfRequest
from projectkoios.simulations.dft.pw.settings import CalculationType
from projectkoios.simulations.dft.pw.simulation import ResolvedPwDftSimulation
from projectkoios.simulations.library.codec import simulation_source_reference
from projectkoios.simulations.structure import StructureResolution

VASP_SCF_INTEGRATION_ID = CalculatorIntegrationId("vasp")


@dataclass(frozen=True, slots=True)
class VaspScfInputProjector:
    """Compose existing INCAR, KPOINTS, POSCAR, and calculation projectors."""

    configuration: VaspScfProjectionConfiguration

    def project(
        self,
        request: PwDftScfRequest,
        structure: StructureResolution,
    ) -> CalculatorInputRecord:
        """Return exact text inputs while leaving POTCAR bytes external."""
        if type(request) is not PwDftScfRequest:
            raise TypeError("request must be a PwDftScfRequest")
        if type(structure) is not StructureResolution:
            raise TypeError("structure must be a StructureResolution")
        specification = request.specification
        simulation = specification.simulation
        resolved = ResolvedPwDftSimulation(simulation=simulation, structure=structure)
        calculation = VaspCalculationProjector().project(CalculationType.scf)
        if not simulation.pseudopotentials:
            raise ValueError("VASP translation requires exact bound pseudopotentials")
        if any(
            item.artifact_format is not PseudopotentialArtifactFormat.VASP_POTCAR
            for item in simulation.pseudopotentials
        ):
            raise ValueError("VASP translation requires POTCAR pseudopotentials")
        config = self.configuration
        occupation_to_ismear = {
            DftOccupationMethod.GAUSSIAN: 0,
            DftOccupationMethod.FERMI_DIRAC: -1,
            DftOccupationMethod.METHFESSEL_PAXTON: 1,
        }
        expected_ismear = occupation_to_ismear.get(specification.occupation.method)
        if expected_ismear is None:
            raise NotImplementedError(
                "VASP SCF translation does not support this occupation method"
            )
        if config.smearing_method != expected_ismear:
            raise ValueError("VASP smearing method must match specification")
        if specification.occupation.smearing_width_ev is not None and (
            config.smearing_width_ev != specification.occupation.smearing_width_ev
        ):
            raise ValueError("VASP smearing width must match specification")
        if (
            config.electronic_tolerance_ev
            != specification.electronic_convergence.energy_tolerance_ev
            or config.maximum_electronic_steps
            != specification.electronic_convergence.maximum_electronic_iterations
        ):
            raise ValueError("VASP electronic convergence must match specification")
        # Current writer relies on VASP's enabled symmetry and time-reversal
        # reduction; explicit disablement needs a separately reviewed mapping.
        if not (
            specification.kpoint_sampling.use_spatial_symmetry
            and specification.kpoint_sampling.use_time_reversal
        ):
            raise NotImplementedError(
                "VASP SCF symmetry-reduction translation is not implemented"
            )
        if simulation.spin.mode not in {
            DftSpinMode.UNPOLARIZED,
            DftSpinMode.COLLINEAR,
        }:
            raise NotImplementedError(
                "VASP SCF translation supports only unpolarized and collinear spin"
            )
        spin_assignments: tuple[IncarAssignment, ...] = (
            IncarAssignment(
                "ISPIN",
                "2" if simulation.spin.mode is DftSpinMode.COLLINEAR else "1",
            ),
        )
        if simulation.spin.constrain_spin_channel_difference:
            spin_assignments += (
                IncarAssignment(
                    "NUPDOWN",
                    str(simulation.spin.spin_channel_electron_difference),
                ),
            )
        if simulation.spin.initial_site_magnetic_moments_mu_b:
            initial_moments = simulation.spin.initial_site_magnetic_moments_mu_b
            spin_assignments += (
                IncarAssignment(
                    "MAGMOM",
                    " ".join(_format_float(value) for value in initial_moments),
                ),
            )
        charge_assignments: tuple[IncarAssignment, ...] = ()
        if simulation.charge.delta_n_electrons != 0:
            if resolved.electron_count is None:
                raise ValueError(
                    "charged VASP SCF translation requires exact pseudopotentials"
                )
            charge_assignments = (
                IncarAssignment(
                    "NELECT", _format_float(float(resolved.electron_count))
                ),
            )
        incar = IncarFile(
            assignments=(
                IncarAssignment("SYSTEM", config.system_label),
                IncarAssignment("ISTART", "0"),
                IncarAssignment("ICHARG", "2"),
                IncarAssignment(
                    "ENCUT",
                    _format_float(specification.wavefunction_cutoff_ev),
                ),
                IncarAssignment("ALGO", config.algorithm),
                IncarAssignment("NELM", str(config.maximum_electronic_steps)),
                IncarAssignment("EDIFF", _format_float(config.electronic_tolerance_ev)),
                IncarAssignment("ISMEAR", str(config.smearing_method)),
                IncarAssignment("SIGMA", _format_float(config.smearing_width_ev)),
                *spin_assignments,
                *charge_assignments,
                IncarAssignment(
                    "LREAL",
                    ".TRUE." if config.real_space_projection else ".FALSE.",
                ),
                *calculation.input_file.assignments,
            )
        )
        poscar = PoscarModel(
            comment=config.poscar_comment,
            unit_cell_model=UnitCellModel(resolved.unit_cell),
        )
        kpoints = VaspAutomaticKpointMesh(
            mesh=specification.kpoint_sampling.mesh,
            shift=specification.kpoint_sampling.shift,
        )
        electronic_convergence = specification.electronic_convergence
        spin = simulation.spin
        rendered = (
            ("incar", "INCAR", IncarWriter().render(incar).encode("ascii")),
            ("kpoints", "KPOINTS", VaspKpointsWriter().render(kpoints).encode("ascii")),
            ("poscar", "POSCAR", PoscarWriter().render(poscar).encode("ascii")),
        )
        source = simulation_source_reference(specification)
        return CalculatorInputRecord(
            input_id=f"{specification.simulation_id}.VASP.PreparedInput",
            schema_version=1,
            source=source,
            integration_id=VASP_SCF_INTEGRATION_ID,
            calculator_name="VASP",
            calculator_version_constraint=">=6,<7",
            representation="vasp-static-scf-input-set",
            artifacts=tuple(
                CalculatorInputArtifact(
                    role=role,
                    filename=filename,
                    media_type="text/plain; charset=us-ascii",
                    content=content,
                    byte_size=len(content),
                    sha256=hashlib.sha256(content).hexdigest(),
                )
                for role, filename, content in rendered
            ),
            external_requirements=tuple(
                CalculatorExternalInputRequirement(
                    role="pseudopotential",
                    stable_id=f"{item.symbol}.{item.sha256}",
                    filename=item.filename,
                    format=item.artifact_format.value,
                    byte_size=item.byte_size,
                    sha256=item.sha256,
                    provenance=f"canonical-simulation-specification:{source.sha256}",
                    element_symbol=item.symbol,
                )
                for item in simulation.pseudopotentials
            ),
            mappings=(
                CalculatorInputMapping(
                    neutral_field="structure",
                    neutral_value=(
                        f"{simulation.structure.structure_id}/"
                        f"{simulation.structure.sha256}"
                    ),
                    native_fields=("POSCAR",),
                    native_values=("cartesian-lattice-and-direct-sites",),
                    effect="encoding",
                    qualification="Exact verified structure geometry is rendered.",
                ),
                CalculatorInputMapping(
                    neutral_field="electronic",
                    neutral_value=json.dumps(
                        {
                            "cutoff_ev": specification.wavefunction_cutoff_ev,
                            "energy_tolerance_ev": (
                                electronic_convergence.energy_tolerance_ev
                            ),
                            "maximum_iterations": (
                                electronic_convergence.maximum_electronic_iterations
                            ),
                            "occupation": specification.occupation.method.value,
                            "smearing_width_ev": (
                                specification.occupation.smearing_width_ev
                            ),
                        },
                        allow_nan=False,
                        separators=(",", ":"),
                        sort_keys=True,
                    ),
                    native_fields=("INCAR",),
                    native_values=("ENCUT/EDIFF/NELM/ISMEAR/SIGMA",),
                    effect="encoding",
                    qualification=calculation.qualification,
                ),
                CalculatorInputMapping(
                    neutral_field="kpoint_sampling",
                    neutral_value=json.dumps(
                        {
                            "mesh": specification.kpoint_sampling.mesh,
                            "shift": specification.kpoint_sampling.shift,
                        },
                        separators=(",", ":"),
                        sort_keys=True,
                    ),
                    native_fields=("KPOINTS",),
                    native_values=("automatic-mesh",),
                    effect="encoding",
                    qualification=(
                        "VASP native symmetry defaults are explicitly qualified."
                    ),
                ),
                CalculatorInputMapping(
                    neutral_field="charge-and-spin",
                    neutral_value=json.dumps(
                        {
                            "charge_state": simulation.charge.charge_state,
                            "initial_site_moments_mu_b": (
                                spin.initial_site_magnetic_moments_mu_b
                            ),
                            "mode": spin.mode.value,
                            "spin_channel_difference": (
                                spin.spin_channel_electron_difference
                            ),
                        },
                        allow_nan=False,
                        separators=(",", ":"),
                        sort_keys=True,
                    ),
                    native_fields=("INCAR.ISPIN", "INCAR.NUPDOWN/MAGMOM/NELECT"),
                    native_values=(
                        "2" if simulation.spin.mode is DftSpinMode.COLLINEAR else "1",
                        "explicit-when-requested",
                    ),
                    effect="encoding",
                    qualification="Unsupported spin modes fail closed.",
                ),
                CalculatorInputMapping(
                    neutral_field="pseudopotentials",
                    neutral_value=json.dumps(
                        [item.sha256 for item in simulation.pseudopotentials],
                        separators=(",", ":"),
                    ),
                    native_fields=("POTCAR",),
                    native_values=(
                        ",".join(item.filename for item in simulation.pseudopotentials),
                    ),
                    effect="external-dependency",
                    qualification="Exact POTCAR bytes remain an external requirement.",
                ),
            ),
            preparation_operation="projectkoios.vasp.pw.scf.prepare",
            preparation_version="1",
        )


def _format_float(value: float) -> str:
    return f"{value:.12g}".replace("e-0", "e-").replace("e+0", "e+")
