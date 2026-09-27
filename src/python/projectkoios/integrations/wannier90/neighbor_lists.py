"""Typed adaptation of Wannier90 ``.nnkp`` neighbor lists."""

from __future__ import annotations

from dataclasses import dataclass

from ._parsing import BoundedParser, decode_text, positive_dimension


@dataclass(frozen=True, slots=True)
class Wannier90NeighborListData:
    """Retain a normalized ordered one-based native neighbor inventory."""

    neighbor_count: int
    records: tuple[tuple[int, int, int, int, int], ...]

    def __post_init__(self) -> None:
        if type(self.neighbor_count) is not int:
            raise TypeError("neighbor_count must be a built-in int")
        if self.neighbor_count <= 0:
            raise ValueError("neighbor_count must be positive")
        if not isinstance(self.records, tuple) or not self.records:
            raise TypeError("records must be a nonempty tuple")
        if len(self.records) % self.neighbor_count != 0:
            raise ValueError("record count must be divisible by neighbor_count")
        kpoint_count = len(self.records) // self.neighbor_count
        for record in self.records:
            if (
                not isinstance(record, tuple)
                or len(record) != 5
                or any(type(value) is not int for value in record)
            ):
                raise TypeError("neighbor records must contain five built-in integers")
            if not (1 <= record[0] <= kpoint_count):
                raise ValueError("source k-point index lies outside inferred count")
            if not (1 <= record[1] <= kpoint_count):
                raise ValueError("target k-point index lies outside inferred count")
        expected_sources = tuple(
            source
            for source in range(1, kpoint_count + 1)
            for _ in range(self.neighbor_count)
        )
        if tuple(record[0] for record in self.records) != expected_sources:
            raise ValueError(
                "each first k point must own neighbor_count records "
                "in normalized native order"
            )
        if len(set(self.records)) != len(self.records):
            raise ValueError("neighbor inventory contains a duplicate record")

    @property
    def kpoint_count(self) -> int:
        return len(self.records) // self.neighbor_count


class Wannier90NeighborListParser(BoundedParser):
    """Parse exactly one bounded ``begin nnkpts`` block."""

    def execute(self, payload: bytes) -> Wannier90NeighborListData:
        text = decode_text(payload, "nnkp", self.limits)
        lines = tuple(line.strip() for line in text.splitlines())
        begins = tuple(
            index for index, line in enumerate(lines) if line == "begin nnkpts"
        )
        ends = tuple(index for index, line in enumerate(lines) if line == "end nnkpts")
        if len(begins) != 1 or len(ends) != 1 or ends[0] <= begins[0]:
            raise ValueError("nnkp payload lacks exactly one complete nnkpts block")
        block = tuple(line for line in lines[begins[0] + 1 : ends[0]] if line)
        if not block:
            raise ValueError("nnkpts block must be nonempty")
        try:
            raw_neighbor_count = int(block[0])
        except ValueError as error:
            raise ValueError("nnkpts neighbor count must be an integer") from error
        neighbor_count = positive_dimension(
            raw_neighbor_count, "neighbor_count", self.limits
        )
        if len(block) - 1 > self.limits.maximum_records:
            raise ValueError("neighbor record count exceeds maximum_records")
        records: list[tuple[int, int, int, int, int]] = []
        for line in block[1:]:
            fields = line.split()
            if len(fields) != 5:
                raise ValueError("nnkpts entry must contain five integers")
            try:
                values = tuple(int(field) for field in fields)
            except ValueError as error:
                raise ValueError("nnkpts entry must contain integers") from error
            records.append((values[0], values[1], values[2], values[3], values[4]))
        if not records or len(records) % neighbor_count:
            raise ValueError("record count must be divisible by neighbor_count")
        positive_dimension(len(records) // neighbor_count, "kpoint_count", self.limits)
        return Wannier90NeighborListData(neighbor_count, tuple(records))
