"""Secure bounded file reads for explicit provenance verification."""

from __future__ import annotations

import os
import stat
from pathlib import Path, PurePosixPath

_MAXIMUM_READ_BYTES = 64 * 1024 * 1024
_READ_CHUNK_BYTES = 1024 * 1024


def read_bounded_regular_file(
    root: Path,
    relative_path: str,
    *,
    maximum_bytes: int,
    label: str,
) -> bytes:
    """Read one root-relative regular file through a pinned descriptor chain."""
    _require_secure_descriptor_support()
    parts = _relative_parts(relative_path)
    if type(maximum_bytes) is not int or not 0 < maximum_bytes <= _MAXIMUM_READ_BYTES:
        raise ValueError("maximum_bytes is outside its supported bound")
    if type(label) is not str or not label or len(label) > 256:
        raise ValueError("evidence label is invalid")
    descriptors: list[int] = []
    try:
        root_descriptor = os.open(root, _directory_flags())
        descriptors.append(root_descriptor)
        if not stat.S_ISDIR(os.fstat(root_descriptor).st_mode):
            raise ValueError(f"{label} root must be a directory")
        directory_descriptor = root_descriptor
        for part in parts[:-1]:
            directory_descriptor = os.open(
                part, _directory_flags(), dir_fd=directory_descriptor
            )
            descriptors.append(directory_descriptor)
            if not stat.S_ISDIR(os.fstat(directory_descriptor).st_mode):
                raise ValueError(f"{label} contains a non-directory path")
        file_descriptor = os.open(parts[-1], _file_flags(), dir_fd=directory_descriptor)
        descriptors.append(file_descriptor)
        before = os.fstat(file_descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError(f"{label} must be a regular file")
        if before.st_size < 0 or before.st_size > maximum_bytes:
            raise ValueError(f"{label} exceeds its byte bound")
        chunks: list[bytes] = []
        size = 0
        while chunk := os.read(file_descriptor, _READ_CHUNK_BYTES):
            size += len(chunk)
            if size > maximum_bytes:
                raise ValueError(f"{label} exceeds its byte bound")
            chunks.append(chunk)
        after = os.fstat(file_descriptor)
        if _identity(before) != _identity(after) or size != before.st_size:
            raise ValueError(f"{label} changed during read")
        return b"".join(chunks)
    except OSError as error:
        raise ValueError(f"{label} is not a safely readable regular file") from error
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _directory_flags() -> int:
    return os.O_RDONLY | os.O_CLOEXEC | os.O_DIRECTORY | os.O_NOFOLLOW


def _file_flags() -> int:
    return os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK


def _require_secure_descriptor_support() -> None:
    required_flags = ("O_CLOEXEC", "O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK")
    if (
        any(not hasattr(os, name) for name in required_flags)
        or os.open not in os.supports_dir_fd
    ):
        raise RuntimeError("secure descriptor-based evidence reads are unsupported")


def _identity(status: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        status.st_dev,
        status.st_ino,
        status.st_mode,
        status.st_size,
        status.st_mtime_ns,
        status.st_ctime_ns,
    )


def _relative_parts(value: str) -> tuple[str, ...]:
    path = PurePosixPath(value)
    if (
        not value
        or value == "."
        or value != path.as_posix()
        or path.is_absolute()
        or "." in path.parts
        or ".." in path.parts
    ):
        raise ValueError("relative_path must be a normalized relative path")
    return path.parts
