r"""Software verification of generic Wannier90 preprocessing input.

Evidence profile: claim_bearing

Bounded artifact scope: immutable typed non-spin spectral input and
deterministic ``.win`` rendering. These checks do not run Wannier90 or validate
a scientific construction.
"""

from __future__ import annotations

import hashlib

import pytest

from projectkoios.integrations.wannier90 import (
    WANNIER90_INTEGRATION_ID,
    Wannier90PreprocessingInput,
)
from projectkoios.physkit.numeric import as_f64_array
from projectkoios.physkit.periodic import DirectLattice3D
from projectkoios.physkit.periodic.unit_cell import Atom, AtomicBasis, UnitCell
from projectkoios.physkit.units import (
    MatrixQuantity,
    PhysicalUnit,
    ScalarQuantity,
    Unitless,
    VectorQuantity,
)
from projectkoios.simulations.calculator_input import CalculatorInputSourceReference

pytestmark = pytest.mark.software_verification
SUT = Wannier90PreprocessingInput
_ANGSTROM = PhysicalUnit("angstrom")
_ANGSTROM_SQUARED = PhysicalUnit("angstrom ** 2")
_ELECTRON_VOLT = PhysicalUnit("eV")


class TestWannier90PreprocessingInput:
    """Own software evidence for typed preprocessing input and rendering."""

    @staticmethod
    def _source() -> CalculatorInputSourceReference:
        return CalculatorInputSourceReference(
            simulation_id="synthetic.wannier90.construction",
            representation="synthetic-test-construction",
            schema_version=1,
            byte_size=1,
            sha256="0" * 64,
        )

    @staticmethod
    def _unit_cell(
        scale_angstrom: float,
        symbol: str,
        fractional_positions: tuple[tuple[float, float, float], ...],
    ) -> UnitCell:
        return UnitCell(
            direct_lattice=DirectLattice3D(
                a1=as_f64_array((1.0, 0.0, 0.0)),
                a2=as_f64_array((0.0, 1.0, 0.0)),
                a3=as_f64_array((0.0, 0.0, 1.0)),
            ),
            lattice_parameter=ScalarQuantity(scale_angstrom, _ANGSTROM),
            atomic_basis=AtomicBasis(
                atoms=tuple(
                    Atom(
                        symbol=symbol,
                        position_fractional=VectorQuantity(
                            as_f64_array(position),
                            Unitless(),
                        ),
                    )
                    for position in fractional_positions
                )
            ),
        )

    @staticmethod
    def _kpoints(
        values: tuple[tuple[float, float, float], ...],
    ) -> MatrixQuantity:
        return MatrixQuantity(as_f64_array(values), Unitless())

    def _isolated_input(
        self,
        *,
        num_bands: int = 1,
        num_wann: int = 1,
        mp_grid: tuple[int, int, int] = (1, 1, 1),
        kpoints: tuple[tuple[float, float, float], ...] = ((0.0, 0.0, 0.0),),
        selected_projection_indices: tuple[int, ...] = (),
    ) -> Wannier90PreprocessingInput:
        return SUT(
            input_id="synthetic.wannier90.preprocessing-input",
            source=self._source(),
            seedname="hydrogen",
            calculator_version_constraint="==3.1.0",
            num_bands=num_bands,
            num_wann=num_wann,
            unit_cell=self._unit_cell(1.0, "H", ((0.0, 0.0, 0.0),)),
            projections=("H:s",),
            mp_grid=mp_grid,
            kpoints_reciprocal_fractional=self._kpoints(kpoints),
            localization_iterations=100,
            localization_tolerance=ScalarQuantity(1.0e-10, _ANGSTROM_SQUARED),
            localization_convergence_window=3,
            write_hr=True,
            selected_projection_indices=selected_projection_indices,
        )

    def test_render__isolated_construction__is_byte_exact(self) -> None:
        """The isolated subset has one deterministic native representation."""
        native_input = self._isolated_input()
        content = native_input.render()
        prepared = native_input.prepare()

        assert native_input.input_filename == "hydrogen.win"
        assert native_input.nnkp_filename == "hydrogen.nnkp"

        assert prepared.integration_id == WANNIER90_INTEGRATION_ID
        assert prepared.integration_id.value == "wannier90"
        assert prepared.calculator_name == "wannier90.x"
        assert prepared.representation == "wannier90-win"
        assert prepared.external_requirements == ()
        assert len(prepared.artifacts) == 1
        artifact = prepared.artifacts[0]
        assert artifact.filename == "hydrogen.win"
        assert content == (
            "num_bands = 1\n"
            "num_wann = 1\n"
            "spinors = .false.\n"
            "num_iter = 100\n"
            "conv_tol = 1e-10\n"
            "conv_window = 3\n"
            "write_hr = .true.\n"
            "length_unit = ang\n"
            "\n"
            "begin unit_cell_cart\n"
            "ang\n"
            "1.0000000000 0.0000000000 0.0000000000\n"
            "0.0000000000 1.0000000000 0.0000000000\n"
            "0.0000000000 0.0000000000 1.0000000000\n"
            "end unit_cell_cart\n"
            "\n"
            "begin atoms_frac\n"
            "H 0.0000000000 0.0000000000 0.0000000000\n"
            "end atoms_frac\n"
            "\n"
            "begin projections\n"
            "H:s\n"
            "end projections\n"
            "\n"
            "mp_grid = 1 1 1\n"
            "\n"
            "begin kpoints\n"
            "0.0000000000 0.0000000000 0.0000000000\n"
            "end kpoints\n"
        ).encode("ascii")
        assert artifact.content == content
        assert artifact.byte_size == len(artifact.content)
        assert artifact.sha256 == hashlib.sha256(artifact.content).hexdigest()
        assert prepared.preparation_operation.endswith(
            "Wannier90PreprocessingInput.prepare"
        )

    def test_render__entangled_construction__preserves_declared_controls(self) -> None:
        """Pint-backed windows and controls render in native units and order."""
        content = SUT(
            input_id="synthetic.entangled",
            source=self._source(),
            seedname="synthetic",
            calculator_version_constraint="==3.1.0",
            num_bands=4,
            num_wann=2,
            unit_cell=self._unit_cell(
                2.0,
                "Si",
                ((0.0, 0.0, 0.0), (0.25, 0.25, 0.25)),
            ),
            projections=("Si:sp3",),
            mp_grid=(2, 1, 1),
            kpoints_reciprocal_fractional=self._kpoints(
                ((0.5, 0.0, 0.0), (0.0, 0.0, 0.0))
            ),
            localization_iterations=200,
            localization_tolerance=ScalarQuantity(1.0e-11, _ANGSTROM_SQUARED),
            localization_convergence_window=4,
            write_hr=False,
            excluded_bands=(1,),
            selected_projection_indices=(2, 1),
            outer_window=(
                ScalarQuantity(-5.0, _ELECTRON_VOLT),
                ScalarQuantity(12.0, _ELECTRON_VOLT),
            ),
            frozen_window=(
                ScalarQuantity(-2.0, _ELECTRON_VOLT),
                ScalarQuantity(5.0, _ELECTRON_VOLT),
            ),
            disentanglement_iterations=300,
            disentanglement_tolerance=ScalarQuantity(1.0e-12, Unitless()),
            disentanglement_convergence_window=5,
            disentanglement_mix_ratio=ScalarQuantity(0.5, Unitless()),
        ).render()

        text = content.decode("ascii")
        assert "exclude_bands = 1\n" in text
        assert "select_projections = 2, 1\n" in text
        assert "dis_win_min = -5\n" in text
        assert "dis_win_max = 12\n" in text
        assert "dis_froz_min = -2\n" in text
        assert "dis_froz_max = 5\n" in text
        assert "dis_num_iter = 300\n" in text
        assert "dis_conv_tol = 1e-12\n" in text
        assert "dis_conv_window = 5\n" in text
        assert "dis_mix_ratio = 0.5\n" in text
        assert "write_hr = .false.\n" in text
        first = text.index("0.5000000000 0.0000000000 0.0000000000")
        second = text.index("0.0000000000 0.0000000000 0.0000000000", first)
        assert first < second

    def test_render__same_construction__is_deterministic(self) -> None:
        """Repeated construction and rendering yield identical identities."""
        first_input = self._isolated_input()
        second_input = self._isolated_input()

        assert first_input.render() == second_input.render()
        first = first_input.prepare()
        second = second_input.prepare()
        assert first == second
        assert first.canonical_bytes == second.canonical_bytes
        assert first.sha256 == second.sha256

    def test_constructor__inconsistent_rank_or_mesh__fails_closed(self) -> None:
        """Invalid ranks and incomplete reciprocal grids fail at construction."""
        with pytest.raises(ValueError, match="num_wann must not exceed"):
            self._isolated_input(num_bands=1, num_wann=2)
        with pytest.raises(ValueError, match="k-point count"):
            self._isolated_input(mp_grid=(2, 1, 1))
        with pytest.raises(ValueError, match="exactly num_wann"):
            self._isolated_input(
                num_bands=2,
                num_wann=2,
                selected_projection_indices=(1,),
            )

    def test_constructor__invalid_disentanglement__fails_closed(self) -> None:
        """Entangled rank requires complete and nested window controls."""
        with pytest.raises(ValueError, match="outer energy window"):
            self._isolated_input(num_bands=2, num_wann=1)

        with pytest.raises(ValueError, match="inside outer_window"):
            SUT(
                input_id="synthetic.entangled",
                source=self._source(),
                seedname="synthetic",
                calculator_version_constraint="==3.1.0",
                num_bands=2,
                num_wann=1,
                unit_cell=self._unit_cell(1.0, "H", ((0.0, 0.0, 0.0),)),
                projections=("H:s",),
                mp_grid=(1, 1, 1),
                kpoints_reciprocal_fractional=self._kpoints(((0.0, 0.0, 0.0),)),
                localization_iterations=100,
                localization_tolerance=ScalarQuantity(
                    1.0e-10,
                    _ANGSTROM_SQUARED,
                ),
                localization_convergence_window=3,
                write_hr=True,
                outer_window=(
                    ScalarQuantity(-5.0, _ELECTRON_VOLT),
                    ScalarQuantity(5.0, _ELECTRON_VOLT),
                ),
                frozen_window=(
                    ScalarQuantity(-6.0, _ELECTRON_VOLT),
                    ScalarQuantity(2.0, _ELECTRON_VOLT),
                ),
                disentanglement_iterations=100,
                disentanglement_tolerance=ScalarQuantity(1.0e-10, Unitless()),
                disentanglement_convergence_window=3,
                disentanglement_mix_ratio=ScalarQuantity(0.5, Unitless()),
            )
