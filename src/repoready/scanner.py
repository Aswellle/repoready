"""Read-only filesystem boundary for repository checks.

The scanner never opens file contents and never executes anything found
in the target tree; it only enumerates paths. Rules (Phase 1+) read
files with their own size limits and error handling.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator

# Frozen skip list; mirrors docs/spec/01-architecture-rules.md §3.
DEFAULT_SKIP_DIRS = frozenset(
    {
        ".git",
        "node_modules",
        "vendor",
        "dist",
        "build",
        "__pycache__",
        ".venv",
        "venv",
        ".tox",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
    }
)


class ScannerError(Exception):
    """Raised when the requested scan root cannot be used."""


def resolve_root(raw: str | os.PathLike[str]) -> Path:
    """Return the absolute resolved scan root, or raise ScannerError."""
    try:
        resolved = Path(raw).resolve(strict=True)
    except OSError as exc:
        raise ScannerError(
            f"cannot access path '{raw}': {exc.strerror or exc}"
        ) from exc
    if not resolved.is_dir():
        raise ScannerError(f"not a directory: '{raw}'")
    return resolved


def iter_files(root: Path) -> Iterator[Path]:
    """Yield file paths under root in deterministic order.

    Directory symlinks are never followed (os.walk(followlinks=False)),
    so the walk cannot leave root through a link. Generated/vendored
    directories from the frozen skip list are pruned.
    """
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = sorted(d for d in dirnames if d not in DEFAULT_SKIP_DIRS)
        for name in sorted(filenames):
            yield Path(dirpath) / name
