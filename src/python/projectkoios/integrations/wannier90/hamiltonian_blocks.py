"""Typed adaptation of Wannier90 ``_hr.dat`` Hamiltonian-block files."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from physkit.units.quantities import ComplexMatrixQuantity, ModelSystemUnit


@dataclass(frozen=True, slots=True, eq=False)
class Wannier90HamiltonianBlockData:
    """Retain native lattice representatives, degeneracies, and Hamiltonian blocks."""

    representatives: tuple[tuple[int, int, int], ...]
    degeneracies: tuple[int, ...]
    blocks: tuple[ComplexMatrixQuantity, ...]

    def __post_init__(self) -> None:
        """Validate native ordering, degeneracies, and homogeneous square blocks."""
        if not isinstance(self.representatives, tuple) or not self.representatives:
            raise TypeError("representatives must be a nonempty tuple")
        for representative in self.representatives:
            if (
                not isinstance(representative, tuple)
                or len(representative) != 3
                or any(type(value) is not int for value in representative)
            ):
                raise TypeError(
                    "representatives must contain integer coordinate triples"
                )
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
        """Return the represented Wannier-orbital count."""
        return int(self.blocks[0].magnitude.shape[0])


class Wannier90HamiltonianBlockParser:
    """Parse one UTF-8 Wannier90 ``_hr.dat`` payload without interpolation."""

    __slots__ = ()

    def execute(
        self, payload: bytes, energy_unit: ModelSystemUnit
    ) -> Wannier90HamiltonianBlockData:
        """Return native blocks while preserving the degeneracy inventory."""
        if type(payload) is not bytes:
            raise TypeError("payload must be bytes")
        try:
            lines = payload.decode("utf-8").splitlines()
        except UnicodeDecodeError as error:
            raise ValueError("Hamiltonian-block payload must be valid UTF-8") from error
        if len(lines) < 3:
            raise ValueError("Hamiltonian-block payload lacks its header")
        try:
            wannier_count = int(lines[1].strip())
            representative_count = int(lines[2].strip())
        except ValueError as error:
            raise ValueError("Hamiltonian-block dimensions must be integers") from error
        if wannier_count <= 0 or representative_count <= 0:
            raise ValueError("Hamiltonian-block dimensions must be positive")
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
        representatives: list[tuple[int, int, int]] = []
        blocks: list[ComplexMatrixQuantity] = []
        entry_count = wannier_count * wannier_count
        for _ in range(representative_count):
            block = np.empty((wannier_count, wannier_count), dtype=np.complex128)
            representative: tuple[int, int, int] | None = None
            occupied: set[tuple[int, int]] = set()
            for _ in range(entry_count):
                if line_index >= len(lines):
                    raise ValueError("payload ends within a Hamiltonian block")
                fields = lines[line_index].split()
                line_index += 1
                if len(fields) != 7:
                    raise ValueError("Hamiltonian entry must contain seven fields")
                try:
                    current = (int(fields[0]), int(fields[1]), int(fields[2]))
                    row = int(fields[3]) - 1
                    column = int(fields[4]) - 1
                    value = complex(float(fields[5]), float(fields[6]))
                except ValueError as error:
                    raise ValueError(
                        "Hamiltonian entry contains an invalid number"
                    ) from error
                if representative is None:
                    representative = current
                elif current != representative:
                    raise ValueError(
                        "all entries in one block must share a representative"
                    )
                if (
                    row < 0
                    or row >= wannier_count
                    or column < 0
                    or column >= wannier_count
                ):
                    raise ValueError("Hamiltonian matrix index lies outside dimensions")
                if (row, column) in occupied:
                    raise ValueError(
                        "Hamiltonian block contains a duplicate matrix entry"
                    )
                occupied.add((row, column))
                block[row, column] = value
            if representative is None:
                raise ValueError("Hamiltonian block is empty")
            representatives.append(representative)
            blocks.append(ComplexMatrixQuantity(block, energy_unit))
        if any(line.strip() for line in lines[line_index:]):
            raise ValueError("Hamiltonian-block payload contains trailing lines")
        return Wannier90HamiltonianBlockData(
            tuple(representatives), tuple(degeneracies), tuple(blocks)
        )
