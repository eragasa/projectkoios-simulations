"""Typed adaptation of Wannier90 ``_hr.dat`` Hamiltonian-block files."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from projectkoios.physkit.units.quantities import ComplexMatrixQuantity, ModelSystemUnit

from ._parsing import (
    BoundedParser,
    checked_product,
    decode_text,
    parse_fortran_real,
    positive_dimension,
)


@dataclass(frozen=True, slots=True, eq=False)
class Wannier90HamiltonianBlockData:
    """Retain native lattice representatives, degeneracies, and blocks."""

    representatives: tuple[tuple[int, int, int], ...]
    degeneracies: tuple[int, ...]
    blocks: tuple[ComplexMatrixQuantity, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.representatives, tuple) or not self.representatives:
            raise TypeError("representatives must be a nonempty tuple")
        for representative in self.representatives:
            if (
                not isinstance(representative, tuple)
                or len(representative) != 3
                or any(type(value) is not int for value in representative)
            ):
                raise TypeError("representatives must contain integer triples")
        if len(set(self.representatives)) != len(self.representatives):
            raise ValueError("representatives must be unique")
        if (
            not isinstance(self.degeneracies, tuple)
            or len(self.degeneracies) != len(self.representatives)
            or any(type(value) is not int for value in self.degeneracies)
        ):
            raise TypeError("one built-in integer degeneracy is required per block")
        if any(value <= 0 for value in self.degeneracies):
            raise ValueError("degeneracies must be positive")
        if not isinstance(self.blocks, tuple) or len(self.blocks) != len(
            self.representatives
        ):
            raise ValueError("one Hamiltonian block is required per representative")
        first = self.blocks[0]
        if type(first) is not ComplexMatrixQuantity:
            raise TypeError("every block must be ComplexMatrixQuantity")
        dimension = first.magnitude.shape[0]
        if dimension == 0 or first.magnitude.shape != (dimension, dimension):
            raise ValueError("Hamiltonian blocks must be nonempty and square")
        for block in self.blocks:
            if type(block) is not ComplexMatrixQuantity:
                raise TypeError("every block must be ComplexMatrixQuantity")
            if block.magnitude.shape != (dimension, dimension):
                raise ValueError("all Hamiltonian blocks must have equal square shape")
            if block.unit != first.unit:
                raise ValueError("all Hamiltonian blocks must use the same unit")

    @property
    def wannier_count(self) -> int:
        return int(self.blocks[0].magnitude.shape[0])


class Wannier90HamiltonianBlockParser(BoundedParser):
    """Parse one bounded UTF-8 Wannier90 ``_hr.dat`` payload."""

    def execute(
        self, payload: bytes, energy_unit: ModelSystemUnit
    ) -> Wannier90HamiltonianBlockData:
        text = decode_text(payload, "Hamiltonian-block", self.limits)
        lines = text.splitlines()
        if len(lines) < 3:
            raise ValueError("Hamiltonian-block payload lacks its header")
        try:
            raw_wannier_count = int(lines[1].strip())
            raw_representative_count = int(lines[2].strip())
        except ValueError as error:
            raise ValueError("Hamiltonian-block dimensions must be integers") from error
        wannier_count = positive_dimension(
            raw_wannier_count, "wannier_count", self.limits
        )
        representative_count = positive_dimension(
            raw_representative_count, "representative_count", self.limits
        )
        total_entry_count = checked_product(
            (representative_count, wannier_count, wannier_count),
            "Hamiltonian-block",
            self.limits,
        )
        line_index = 3
        degeneracies: list[int] = []
        while len(degeneracies) < representative_count:
            if line_index >= len(lines):
                raise ValueError("payload ends within the degeneracy inventory")
            try:
                degeneracies.extend(int(value) for value in lines[line_index].split())
            except ValueError as error:
                raise ValueError("degeneracies must be integers") from error
            line_index += 1
        if len(degeneracies) != representative_count:
            raise ValueError("degeneracy inventory exceeds representative count")
        entries = tuple(line for line in lines[line_index:] if line.strip())
        if len(entries) < total_entry_count:
            raise ValueError("payload ends within a Hamiltonian block")
        if len(entries) > total_entry_count:
            raise ValueError("Hamiltonian-block payload contains trailing records")
        representatives: list[tuple[int, int, int]] = []
        blocks: list[ComplexMatrixQuantity] = []
        entry_index = 0
        block_entry_count = wannier_count * wannier_count
        for _ in range(representative_count):
            parsed: list[tuple[int, int, complex]] = []
            representative: tuple[int, int, int] | None = None
            occupied: set[tuple[int, int]] = set()
            for _ in range(block_entry_count):
                fields = entries[entry_index].split()
                entry_index += 1
                if len(fields) != 7:
                    raise ValueError("Hamiltonian entry must contain seven fields")
                try:
                    current = (int(fields[0]), int(fields[1]), int(fields[2]))
                    row = int(fields[3]) - 1
                    column = int(fields[4]) - 1
                except ValueError as error:
                    raise ValueError(
                        "Hamiltonian indices must contain integers"
                    ) from error
                value = complex(
                    parse_fortran_real(fields[5], "Hamiltonian real part"),
                    parse_fortran_real(fields[6], "Hamiltonian imaginary part"),
                )
                if representative is None:
                    representative = current
                elif current != representative:
                    raise ValueError(
                        "all entries in one block must share a representative"
                    )
                if not (0 <= row < wannier_count and 0 <= column < wannier_count):
                    raise ValueError("Hamiltonian matrix index lies outside dimensions")
                if (row, column) in occupied:
                    raise ValueError(
                        "Hamiltonian block contains a duplicate matrix entry"
                    )
                occupied.add((row, column))
                parsed.append((row, column, value))
            if representative is None:
                raise ValueError("Hamiltonian block is empty")
            block: npt.NDArray[np.complex128] = np.empty(
                (wannier_count, wannier_count), dtype=np.complex128
            )
            for row, column, value in parsed:
                block[row, column] = value
            representatives.append(representative)
            blocks.append(ComplexMatrixQuantity(block, energy_unit))
        return Wannier90HamiltonianBlockData(
            tuple(representatives), tuple(degeneracies), tuple(blocks)
        )
