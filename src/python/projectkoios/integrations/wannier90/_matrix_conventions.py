"""Shared native Wannier90 matrix conventions."""

from __future__ import annotations

from enum import StrEnum


class Wannier90MatrixStorageOrder(StrEnum):
    """Native serialization order shared by ``_u.mat`` and ``_u_dis.mat``."""

    first_index_fastest = "first-index-fastest-fortran-order"
