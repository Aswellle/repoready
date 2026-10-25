"""Shared markdown text utilities for README checks.

Only fenced code blocks (``` and ~~~) are excluded from analysis;
indented code blocks and other exotic constructs are covered by the
documented MVP limitations (docs/false-positives.md).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

# Frozen read limit for README/Markdown content
# (docs/spec/01-architecture-rules.md §3).
README_SIZE_LIMIT = 2 * 1024 * 1024

_FENCE_OPEN = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})")
_FENCE_CLOSE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})[ \t]*$")


def iter_unfenced_lines(text: str) -> Iterator[tuple[int, str]]:
    """Yield (1-based line number, line) outside fenced code blocks.

    A fence opens on any line starting (with up to 3 spaces) with a run
    of >= 3 backticks or tildes; it closes on the next bare run of the
    same character that is at least as long. Opening fences may carry an
    info string; closing fences may not.
    """
    fence_char = ""
    fence_len = 0
    for lineno, line in enumerate(text.splitlines(), start=1):
        if fence_char:
            close = _FENCE_CLOSE.match(line)
            if (
                close
                and close.group(1)[0] == fence_char
                and len(close.group(1)) >= fence_len
            ):
                fence_char = ""
            continue
        open_fence = _FENCE_OPEN.match(line)
        if open_fence:
            fence_char = open_fence.group(1)[0]
            fence_len = len(open_fence.group(1))
            continue
        yield lineno, line


def has_fenced_code(text: str) -> bool:
    """Return True when the text contains at least one fenced block."""
    fence_char = ""
    fence_len = 0
    opened = False
    for line in text.splitlines():
        if fence_char:
            close = _FENCE_CLOSE.match(line)
            if (
                close
                and close.group(1)[0] == fence_char
                and len(close.group(1)) >= fence_len
            ):
                fence_char = ""
            continue
        open_fence = _FENCE_OPEN.match(line)
        if open_fence:
            fence_char = open_fence.group(1)[0]
            fence_len = len(open_fence.group(1))
            opened = True
    return opened


def read_capped(path: Path) -> tuple[str, bool]:
    """Read text capped at README_SIZE_LIMIT; return (text, truncated).

    Decoding uses errors="replace" so a non-UTF-8 README degrades to a
    readable-but-lossy analysis instead of crashing the scan.
    """
    size = path.stat().st_size
    if size <= README_SIZE_LIMIT:
        return path.read_text(encoding="utf-8", errors="replace"), False
    with path.open("rb") as handle:
        data = handle.read(README_SIZE_LIMIT)
    return data.decode("utf-8", errors="replace"), True
