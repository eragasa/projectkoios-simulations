"""Typed adaptation of Wannier90 ``.nnkp`` neighbor lists."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Wannier90NeighborListData:
    """Retain ordered one-based native neighbor records and reciprocal shifts."""

    neighbor_count: int
    records: tuple[tuple[int, int, int, int, int], ...]

    def __post_init__(self) -> None:
        """Validate positive indices and complete equal-size neighbor groups."""
        if type(self.neighbor_count) is not int:
            raise TypeError("neighbor_count must be a built-in int")
        if self.neighbor_count <= 0:
            raise ValueError("neighbor_count must be positive")
        if not isinstance(self.records, tuple) or not self.records:
            raise TypeError("records must be a nonempty tuple")
        if len(self.records) % self.neighbor_count != 0:
            raise ValueError("record count must be divisible by neighbor_count")
        for record in self.records:
            if (
                not isinstance(record, tuple)
                or len(record) != 5
                or any(type(value) is not int for value in record)
            ):
                raise TypeError("neighbor records must contain five built-in integers")
            if record[0] <= 0 or record[1] <= 0:
                raise ValueError(
                    "native k-point indices must be one-based and positive"
                )
        kpoint_count = len(self.records) // self.neighbor_count
        counts = tuple(
            sum(record[0] == kpoint for record in self.records)
            for kpoint in range(1, kpoint_count + 1)
        )
        if any(count != self.neighbor_count for count in counts):
            raise ValueError("each first k point must own neighbor_count records")

    @property
    def kpoint_count(self) -> int:
        """Return the inferred reciprocal-point count."""
        return len(self.records) // self.neighbor_count


class Wannier90NeighborListParser:
    """Parse the ``begin nnkpts`` block from caller-supplied UTF-8 bytes."""

    __slots__ = ()

    def execute(self, payload: bytes) -> Wannier90NeighborListData:
        """Return the declared neighbor count and ordered five-integer records."""
        if type(payload) is not bytes:
            raise TypeError("payload must be bytes")
        try:
            lines = tuple(line.strip() for line in payload.decode("utf-8").splitlines())
        except UnicodeDecodeError as error:
            raise ValueError("nnkp payload must be valid UTF-8") from error
        try:
            begin = lines.index("begin nnkpts")
            end = lines.index("end nnkpts", begin + 1)
        except ValueError as error:
            raise ValueError("nnkp payload lacks one complete nnkpts block") from error
        block = tuple(line for line in lines[begin + 1 : end] if line)
        if not block:
            raise ValueError("nnkpts block must be nonempty")
        try:
            neighbor_count = int(block[0])
        except ValueError as error:
            raise ValueError("nnkpts neighbor count must be an integer") from error
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
        return Wannier90NeighborListData(neighbor_count, tuple(records))
