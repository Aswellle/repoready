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

_ATX_HEADING = re.compile(r"^[ \t]{0,3}(#{1,6})[ \t]+(.*)$")
_SETEXT_UNDERLINE = re.compile(r"^[ \t]{0,3}(=+|-+)[ \t]*$")
_THEMATIC_BREAK = re.compile(r"^[ \t]{0,3}([*_])([ \t]*\1){2,}[ \t]*$")
_HTML_ANCHOR = re.compile(
    r"<(?:h[1-6]|a)\b[^>]*\b(?:name|id)\s*=\s*[\"']([^\"']+)[\"']", re.IGNORECASE
)
_HTML_H1 = re.compile(r"<h1\b", re.IGNORECASE)


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


def iter_headings(text: str) -> Iterator[tuple[int, int, str]]:
    """Yield (line number, level, text) for ATX and setext headings.

    Setext support covers the H1 ("text" + ===) and H2 ("text" + ---)
    forms used by mature READMEs and plain-text changelogs. The previous
    non-blank line becomes the heading text; blank lines and thematic
    breaks reset it. HTML headings are not yielded here (see
    html_anchor_names / has_html_h1 for the GitHub-recognised HTML
    forms).
    """
    prev: tuple[int, str] | None = None
    for lineno, line in iter_unfenced_lines(text):
        atx = _ATX_HEADING.match(line)
        if atx:
            yield lineno, len(atx.group(1)), atx.group(2).strip()
            prev = None
            continue
        underline = _SETEXT_UNDERLINE.match(line)
        if underline and prev is not None:
            level = 1 if underline.group(1)[0] == "=" else 2
            yield prev[0], level, prev[1]
            prev = None
            continue
        if not line.strip() or _THEMATIC_BREAK.match(line):
            prev = None
            continue
        prev = (lineno, line.strip())


def html_anchor_names(text: str) -> set[str]:
    """Anchor targets defined via HTML <h1-6>/<a> name or id attributes.

    GitHub honours these as link targets (ripgrep's FAQ uses them).
    Only unfenced lines are considered.
    """
    names: set[str] = set()
    for _, line in iter_unfenced_lines(text):
        names.update(m.group(1) for m in _HTML_ANCHOR.finditer(line))
    return names


def has_html_h1(text: str) -> bool:
    """True when any unfenced line contains an <h1> HTML heading."""
    for _, line in iter_unfenced_lines(text):
        if _HTML_H1.search(line):
            return True
    return False


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
