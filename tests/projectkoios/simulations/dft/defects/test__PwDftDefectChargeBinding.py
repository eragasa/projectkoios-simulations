from __future__ import annotations

import numpy as np
import pytest

from projectkoios.physkit.periodic import DirectLattice3D
from projectkoios.physkit.periodic.unit_cell import Atom, AtomicBasis, UnitCell
from projectkoios.physkit.units import (
    PhysicalUnit,
    ScalarQuantity,
    Unitless,
    VectorQuantity,
)
from projectkoios.simulations.dft.defects import PwDftDefectChargeBinding
from projectkoios.simulations.dft.electronic import (
    DftChargeState,
    DftSpinMode,
    DftSpinTreatment,
)
from projectkoios.simulations.dft.pseudopotential import (
    Pseudopotential,
    PseudopotentialArtifactFormat,
    PseudopotentialFile,
)
from projectkoios.simulations.dft.pw.simulation import ResolvedPwDftSimulation
from projectkoios.simulations.structure.defect import (
    UnitCellDefectDelta,
    UnitCellDefectDeltaApplicator,
    UnitCellDefectDeltaResult,
)
from tests.projectkoios.simulations.dft.pw.support import (
    resolved_pw_dft_simulation,
)


def _atom(symbol: str, position: tuple[float, float, float]) -> Atom:
    return Atom(
        symbol=symbol,
        position_fractional=VectorQuantity(np.array(position), Unitless()),
    )


def _pseudo(symbol: str, valence: int, digit: str) -> PseudopotentialFile:
    return PseudopotentialFile(
        pseudopotential=Pseudopotential(
            symbol=symbol,
            exchange_correlation="PBE",
            formalism="PAW",
            relativistic_treatment="scalar-relativistic",
            valence_electrons=valence,
        ),
        artifact_format=PseudopotentialArtifactFormat.UPF,
        artifact_format_version="2.0.1",
        filename=f"{symbol}.upf",
        sha256=digit * 64,
        byte_size=100,
    )


def _neutral_si_dopant_simulation(
    dopant: str,
    dopant_valence: int,
    spin: DftSpinTreatment,
) -> tuple[UnitCellDefectDeltaResult, ResolvedPwDftSimulation]:
    bulk = UnitCell(
        direct_lattice=DirectLattice3D(
            a1=np.array([1.0, 0.0, 0.0]),
            a2=np.array([0.0, 1.0, 0.0]),
            a3=np.array([0.0, 0.0, 1.0]),
        ),
        lattice_parameter=ScalarQuantity(5.43, PhysicalUnit("angstrom")),
        atomic_basis=AtomicBasis(
            atoms=(
                _atom("Si", (0.0, 0.0, 0.0)),
                _atom("Si", (0.25, 0.25, 0.25)),
            )
        ),
    )
    result = UnitCellDefectDeltaApplicator().action(
        request=UnitCellDefectDelta(
            bulk_cell=bulk,
            removals=(0,),
            additions=(_atom(dopant, (0.0, 0.0, 0.0)),),
        )
    )
    simulation = resolved_pw_dft_simulation(
        result.unit_cell,
        charge=DftChargeState(),
        spin=spin,
        pseudopotentials=(
            _pseudo(dopant, dopant_valence, "2"),
            _pseudo("Si", 4, "1"),
        ),
    )
    return result, simulation


@pytest.mark.parametrize(("dopant", "valence"), (("B", 3), ("P", 5)))
def test_neutral_si_dopants_require_explicit_doublets(
    dopant: str,
    valence: int,
) -> None:
    defect, simulation = _neutral_si_dopant_simulation(
        dopant,
        valence,
        DftSpinTreatment(
            mode=DftSpinMode.COLLINEAR,
            spin_channel_electron_difference=1,
            constrain_spin_channel_difference=True,
        ),
    )

    binding = PwDftDefectChargeBinding(defect=defect, simulation=simulation)

    assert binding.simulation.electron_count in {7, 9}
    assert binding.simulation.simulation.charge.delta_n_electrons == 0


@pytest.mark.parametrize(("dopant", "valence"), (("B", 3), ("P", 5)))
def test_odd_electron_simulation_rejects_unpolarized_default(
    dopant: str,
    valence: int,
) -> None:
    with pytest.raises(ValueError, match="incompatible parity"):
        _neutral_si_dopant_simulation(dopant, valence, DftSpinTreatment())


@pytest.mark.parametrize(("dopant", "valence"), (("B", 3), ("P", 5)))
def test_neutral_si_dopants_reject_non_doublet_collinear_states(
    dopant: str,
    valence: int,
) -> None:
    defect, simulation = _neutral_si_dopant_simulation(
        dopant,
        valence,
        DftSpinTreatment(
            mode=DftSpinMode.COLLINEAR,
            spin_channel_electron_difference=3,
            constrain_spin_channel_difference=True,
        ),
    )

    with pytest.raises(ValueError, match="collinear doublet"):
        PwDftDefectChargeBinding(defect=defect, simulation=simulation)


def test_charge_state_sign_invariant() -> None:
    with pytest.raises(ValueError, match="must equal -delta_n_electrons"):
        DftChargeState(delta_n_electrons=1, charge_state=1)
