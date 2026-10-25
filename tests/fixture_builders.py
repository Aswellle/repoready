"""Runtime fixture builders for tests (Phase 0 fixture list, docs/spec/02).

Fixtures are built inside per-test temp directories; nothing here
touches real user directories. Static golden fixtures land in
tests/fixtures/ from Phase 1 onward.
"""

from __future__ import annotations

import os
from pathlib import Path

OVERSIZED_MARKDOWN_BYTES = 2 * 1024 * 1024 + 1


def make_empty_repo(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    return root


def make_repo_missing_license(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "README.md").write_text("# demo\n", encoding="utf-8")
    (root / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    return root


def make_repo_with_unreadable_file(root: Path) -> Path:
    """Create a file and try to strip read permission.

    On platforms without POSIX mode support (Windows) the chmod may be a
    no-op or only flip the read-only attribute; the fixture still
    exercises enumeration without opening the file. Callers must restore
    access in addCleanup (see test_scanner.py) so temp cleanup works.
    """
    root.mkdir(parents=True, exist_ok=True)
    target = root / "locked.txt"
    target.write_text("secret\n", encoding="utf-8")
    try:
        os.chmod(target, 0o000)
    except OSError:
        pass
    return root


def make_repo_with_symlink_escape(
    root: Path, outside_dir: Path
) -> Path | None:
    """Symlink root/linked -> outside_dir containing secret.txt.

    Returns the link path, or None when the platform cannot create
    symlinks (Windows without admin/developer mode). Callers skip the
    test in that case.
    """
    root.mkdir(parents=True, exist_ok=True)
    outside_dir.mkdir(parents=True, exist_ok=True)
    (outside_dir / "secret.txt").write_text("outside\n", encoding="utf-8")
    link = root / "linked"
    try:
        os.symlink(outside_dir, link, target_is_directory=True)
    except OSError:
        return None
    return link


def make_repo_with_oversized_markdown(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "README.md").write_text("x" * OVERSIZED_MARKDOWN_BYTES, encoding="utf-8")
    return root


def make_repo_with_windows_style_paths(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    nested = root / "docs with spaces" / "中文 (v2)"
    nested.mkdir(parents=True, exist_ok=True)
    (nested / "note.md").write_text("note\n", encoding="utf-8")
    return root


def make_repo_with_never_execute_payload(root: Path) -> Path:
    """A module that would leave a marker if anything imported it."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "evil.py").write_text(
        "open('EXECUTED_MARKER', 'w').write('1')\n", encoding="utf-8"
    )
    return root
