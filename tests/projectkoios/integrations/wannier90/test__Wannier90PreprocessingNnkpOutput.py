r"""Software verification of observed preprocessing topology output.

Evidence profile: claim_bearing

Bounded artifact scope: synthetic NNKP byte observation, seed binding, bounded
parser delegation, and named source-semantic verification. No calculator is
executed and no scientific construction is validated.
"""

from __future__ import annotations

import hashlib
import math

import pytest

from projectkoios.integrations.wannier90 import (
    Wannier90NnkpData,
    Wannier90ParserLimits,
    Wannier90PreprocessingInput,
    Wannier90PreprocessingNnkpOutput,
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
SUT = Wannier90PreprocessingNnkpOutput
_ANGSTROM = PhysicalUnit("angstrom")
_INVERSE_ANGSTROM = PhysicalUnit("1 / angstrom")
_ANGSTROM_SQUARED = PhysicalUnit("angstrom ** 2")


class TestWannier90PreprocessingNnkpOutput:
    """Own evidence for observed preprocessing output and bounded parsing."""

    @staticmethod
    def _payload() -> bytes:
        return b"""generated synthetic interface
begin real_lattice
1.0 0.0 0.0
0.0 1.0 0.0
0.0 0.0 1.0
end real_lattice
begin recip_lattice
6.283185307179586 0.0 0.0
0.0 6.283185307179586 0.0
0.0 0.0 6.283185307179586
end recip_lattice
begin kpoints
2
0.0 0.0 0.0
0.5 0.0 0.0
end kpoints
begin projections
1
0.0 0.0 0.0 0 1 1
0.0 0.0 1.0 1.0 0.0 0.0 1.0
end projections
begin nnkpts
1
1 2 0 0 0
2 1 1 0 0
end nnkpts
begin exclude_bands
1
2
end exclude_bands
"""

    @staticmethod
    def _preprocessing_input(
        direct_lattice: DirectLattice3D | None = None,
        selected_projection_indices: tuple[int, ...] = (),
    ) -> Wannier90PreprocessingInput:
        source = CalculatorInputSourceReference(
            simulation_id="synthetic.wannier90.construction",
            representation="synthetic-test-construction",
            schema_version=1,
            byte_size=1,
            sha256="0" * 64,
        )
        if direct_lattice is None:
            direct_lattice = DirectLattice3D(
                a1=as_f64_array((1.0, 0.0, 0.0)),
                a2=as_f64_array((0.0, 1.0, 0.0)),
                a3=as_f64_array((0.0, 0.0, 1.0)),
            )
        unit_cell = UnitCell(
            direct_lattice=direct_lattice,
            lattice_parameter=ScalarQuantity(1.0, _ANGSTROM),
            atomic_basis=AtomicBasis(
                atoms=(
                    Atom(
                        symbol="H",
                        position_fractional=VectorQuantity(
                            as_f64_array((0.0, 0.0, 0.0)),
                            Unitless(),
                        ),
                    ),
                )
            ),
        )
        return Wannier90PreprocessingInput(
            input_id="synthetic.wannier90.preprocessing-input",
            source=source,
            seedname="synthetic",
            calculator_version_constraint="==3.1.0",
            num_bands=1,
            num_wann=1,
            unit_cell=unit_cell,
            projections=("H:s",),
            mp_grid=(2, 1, 1),
            kpoints_reciprocal_fractional=MatrixQuantity(
                as_f64_array(((0.0, 0.0, 0.0), (0.5, 0.0, 0.0))),
                Unitless(),
            ),
            localization_iterations=100,
            localization_tolerance=ScalarQuantity(1.0e-10, _ANGSTROM_SQUARED),
            localization_convergence_window=3,
            write_hr=True,
            excluded_bands=(2,),
            selected_projection_indices=selected_projection_indices,
        )

    @classmethod
    def _output(
        cls,
        payload: bytes,
        parser_limits: Wannier90ParserLimits | None = None,
        direct_lattice: DirectLattice3D | None = None,
        selected_projection_indices: tuple[int, ...] = (),
    ) -> Wannier90PreprocessingNnkpOutput:
        preprocessing_input = cls._preprocessing_input(
            direct_lattice,
            selected_projection_indices,
        )
        if parser_limits is None:
            return SUT(preprocessing_input=preprocessing_input, content=payload)
        return SUT(
            preprocessing_input=preprocessing_input,
            content=payload,
            parser_limits=parser_limits,
        )

    @staticmethod
    def _verify_named_semantics(
        output: Wannier90PreprocessingNnkpOutput,
    ) -> Wannier90NnkpData:
        return output.verify_source_lattices_kpoints_and_excluded_bands(
            direct_lattice_absolute_tolerance=ScalarQuantity(0.0, _ANGSTROM),
            reciprocal_lattice_absolute_tolerance=ScalarQuantity(
                0.0,
                _INVERSE_ANGSTROM,
            ),
            kpoint_fractional_absolute_tolerance=ScalarQuantity(0.0, Unitless()),
        )

    def test_parse__observed_output__reports_bytes_and_native_order(self) -> None:
        """Observed synthetic bytes expose checksums and bounded parsed data."""
        payload = self._payload()
        output = self._output(payload)

        parsed = output.parse()

        assert output.seedname == "synthetic"
        assert output.filename == "synthetic.nnkp"
        assert output.byte_size == len(payload)
        assert output.sha256 == hashlib.sha256(payload).hexdigest()
        assert parsed.kpoints == ((0.0, 0.0, 0.0), (0.5, 0.0, 0.0))
        assert parsed.neighbors[0].source_kpoint_index == 1
        assert parsed.neighbors[1].source_kpoint_index == 2
        assert parsed.excluded_bands == (2,)

    def test_verify_selected_projection_indices__outside_inventory__fails_closed(
        self,
    ) -> None:
        """Selected source indices must address generated native projections."""
        output = self._output(
            self._payload(),
            selected_projection_indices=(2,),
        )

        with pytest.raises(ValueError, match="exceeds the native projection"):
            output.verify_source_selected_projection_indices()

    def test_verify_named_semantics__matching_data__returns_parsed_data(self) -> None:
        """Direct, reciprocal, k-point, and excluded-band data verify."""
        verified = self._verify_named_semantics(self._output(self._payload()))

        assert verified.kpoint_count == 2
        assert verified.reciprocal_lattice[0][0] == pytest.approx(math.tau)
        assert verified.excluded_bands == (2,)

    def test_verify_named_semantics__skew_lattice__uses_physkit_reciprocal(
        self,
    ) -> None:
        """A skew cell verifies the PhysKit reciprocal-vector convention."""
        payload = self._payload().replace(
            b"""begin real_lattice
1.0 0.0 0.0
0.0 1.0 0.0
0.0 0.0 1.0
end real_lattice
begin recip_lattice
6.283185307179586 0.0 0.0
0.0 6.283185307179586 0.0
0.0 0.0 6.283185307179586
end recip_lattice""",
            b"""begin real_lattice
1.0 0.0 0.0
0.5 1.0 0.0
0.0 0.0 2.0
end real_lattice
begin recip_lattice
6.283185307179586 -3.141592653589793 0.0
0.0 6.283185307179586 0.0
0.0 0.0 3.141592653589793
end recip_lattice""",
        )
        direct_lattice = DirectLattice3D(
            a1=as_f64_array((1.0, 0.0, 0.0)),
            a2=as_f64_array((0.5, 1.0, 0.0)),
            a3=as_f64_array((0.0, 0.0, 2.0)),
        )

        verified = self._verify_named_semantics(
            self._output(payload, direct_lattice=direct_lattice)
        )

        assert verified.reciprocal_lattice[0] == pytest.approx(
            (math.tau, -math.pi, 0.0)
        )

    def test_verify_named_semantics__changed_kpoint__fails_closed(self) -> None:
        """Parsed reciprocal points must match the source declaration in order."""
        payload = self._payload().replace(b"0.5 0.0 0.0", b"0.25 0.0 0.0", 1)

        with pytest.raises(ValueError, match="k-points disagree"):
            self._verify_named_semantics(self._output(payload))

    def test_verify_named_semantics__changed_reciprocal_lattice__fails_closed(
        self,
    ) -> None:
        """Native reciprocal vectors must include the declared two-pi convention."""
        payload = self._payload().replace(b"6.283185307179586", b"6.2", 1)

        with pytest.raises(ValueError, match="reciprocal lattice disagrees"):
            self._verify_named_semantics(self._output(payload))

    def test_parse__declared_parser_limit__is_enforced(self) -> None:
        """Observed bytes remain subject to caller-selected resource bounds."""
        payload = self._payload()
        output = self._output(
            payload,
            Wannier90ParserLimits(maximum_payload_bytes=len(payload) - 1),
        )

        with pytest.raises(ValueError, match="maximum_payload_bytes"):
            output.parse()
