"""Repository-root discovery for tests at arbitrary mirrored depths."""

from pathlib import Path


def find_repository_root(start: Path) -> Path:
    """Find the nearest ancestor carrying this repository's project metadata."""
    resolved = start.resolve()
    candidates = (resolved, *resolved.parents)
    for candidate in candidates:
        if (candidate / "pyproject.toml").is_file() and (
            candidate / "TRANSFER.toml"
        ).is_file():
            return candidate
    raise RuntimeError(f"could not locate repository root from {start}")


REPOSITORY_ROOT = find_repository_root(Path(__file__))
