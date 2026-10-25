"""Top-level filesystem snapshot handed to rule functions.

Rules only see entry listings of the directories they need; nothing is
read or executed. Directory symlinks are recorded with
is_dir(follow_symlinks=False), so a symlinked .github is treated as
absent (symlinks are not followed, per the architecture rules).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Entry:
    name: str
    is_dir: bool


@dataclass(frozen=True)
class ScanContext:
    root: Path
    root_entries: tuple[Entry, ...]
    has_github_dir: bool
    github_entries: tuple[Entry, ...]
    workflows_files: tuple[str, ...]
    issue_template_files: tuple[str, ...]
    docs_entries: tuple[Entry, ...]

    @property
    def root_files_lower(self) -> frozenset[str]:
        return frozenset(e.name.lower() for e in self.root_entries if not e.is_dir)

    @property
    def root_dirs_lower(self) -> frozenset[str]:
        return frozenset(e.name.lower() for e in self.root_entries if e.is_dir)

    @property
    def root_file_names(self) -> tuple[str, ...]:
        return tuple(e.name for e in self.root_entries if not e.is_dir)

    @property
    def github_files_lower(self) -> frozenset[str]:
        return frozenset(e.name.lower() for e in self.github_entries if not e.is_dir)

    @property
    def github_dirs_lower(self) -> frozenset[str]:
        return frozenset(e.name.lower() for e in self.github_entries if e.is_dir)

    @property
    def docs_files_lower(self) -> frozenset[str]:
        return frozenset(e.name.lower() for e in self.docs_entries if not e.is_dir)


def _list_entries(path: Path) -> tuple[Entry, ...]:
    """Snapshot one directory level; unreadable directories look empty."""
    try:
        with os.scandir(path) as it:
            return tuple(
                sorted(
                    (
                        Entry(name=e.name, is_dir=e.is_dir(follow_symlinks=False))
                        for e in it
                    ),
                    key=lambda entry: entry.name,
                )
            )
    except OSError:
        return ()


def build_context(root: Path) -> ScanContext:
    root_entries = _list_entries(root)
    has_github_dir = any(
        e.name == ".github" and e.is_dir for e in root_entries
    )
    github_entries: tuple[Entry, ...] = ()
    workflows_files: tuple[str, ...] = ()
    issue_template_files: tuple[str, ...] = ()
    if has_github_dir:
        github_dir = root / ".github"
        github_entries = _list_entries(github_dir)
        if any(e.name.lower() == "workflows" and e.is_dir for e in github_entries):
            workflows_files = tuple(
                e.name for e in _list_entries(github_dir / "workflows") if not e.is_dir
            )
        if any(
            e.name.lower() == "issue_template" and e.is_dir
            for e in github_entries
        ):
            issue_template_files = tuple(
                e.name
                for e in _list_entries(github_dir / "ISSUE_TEMPLATE")
                if not e.is_dir
            )
    docs_dir = root / "docs"
    docs_entries = (
        _list_entries(docs_dir)
        if any(e.name.lower() == "docs" and e.is_dir for e in root_entries)
        else ()
    )
    return ScanContext(
        root=root,
        root_entries=root_entries,
        has_github_dir=has_github_dir,
        github_entries=github_entries,
        workflows_files=workflows_files,
        issue_template_files=issue_template_files,
        docs_entries=docs_entries,
    )
