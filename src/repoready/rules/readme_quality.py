"""README structure heuristics (docs/spec/01-architecture-rules.md §2).

These checks look for structural signals only. Findings are worded as
"not detected"; absence of a signal must never be reported as proof
that documentation is missing or bad. All checks return None (skipped)
when the repository has no README.

Heading detection covers ATX (#), setext (text + ===/---) and the
HTML <h1> form; fenced code blocks are excluded. Remaining limitations
(indented code blocks, logo-only titles) are documented in
docs/false-positives.md.
"""

from __future__ import annotations

from repoready.rules.registry import make_finding

from .context import ScanContext
from .markdown_text import (
    README_SIZE_LIMIT,
    has_fenced_code,
    has_html_h1,
    iter_headings,
    iter_unfenced_lines,
    read_capped,
)
from .repository_files import find_readme

# Substring keywords (case-insensitive) considered install/run signals.
INSTALL_KEYWORDS = (
    "install",
    "installation",
    "getting started",
    "quickstart",
    "quick start",
    "setup",
    "requirements",
)
# Substring keywords or any fenced code block count as a usage signal.
USAGE_KEYWORDS = (
    "usage",
    "example",
    "examples",
    "demo",
    "getting started",
    "quick start",
    "quickstart",
    "command line",
    "cli",
)

def _scan_readme(ctx: ScanContext):
    """Return (path, text, truncated) or None when there is no README."""
    readme = find_readme(ctx)
    if readme is None:
        return None
    text, truncated = read_capped(readme)
    return readme, text, truncated


def check_no_h1(ctx: ScanContext):
    scan = _scan_readme(ctx)
    if scan is None:
        return None
    readme, text, _ = scan
    for _, level, _text in iter_headings(text):
        if level == 1:
            return []
    if has_html_h1(text):
        return []
    return [
        make_finding(
            "readme.no-h1",
            title="No H1 heading detected in README",
            detail=(
                "No top-level heading was detected; renderers typically use "
                "the first H1 as the project title."
            ),
            path=readme.name,
            evidence=(
                "No ATX '#', setext underline or HTML <h1> heading was "
                "found outside fenced code blocks."
            ),
            suggestion="Start the README with a '# Project Name' heading.",
        )
    ]


def check_install(ctx: ScanContext):
    scan = _scan_readme(ctx)
    if scan is None:
        return None
    readme, text, _ = scan
    for _, line in iter_unfenced_lines(text):
        lowered = line.lower()
        if any(keyword in lowered for keyword in INSTALL_KEYWORDS):
            return []
    return [
        make_finding(
            "readme.install-not-detected",
            title="No install instructions detected",
            detail=(
                "No install-related section or keyword was detected. This "
                "is a structural heuristic and may miss unconventional "
                "wording."
            ),
            path=readme.name,
            evidence=(
                "Checked unfenced lines for install-related keywords "
                "(install, getting started, quick start, setup, "
                "requirements); none found."
            ),
            suggestion=(
                "Add an Install section with a verified command (for "
                "example 'pip install <package>')."
            ),
        )
    ]


def check_usage(ctx: ScanContext):
    scan = _scan_readme(ctx)
    if scan is None:
        return None
    readme, text, _ = scan
    for _, line in iter_unfenced_lines(text):
        lowered = line.lower()
        if any(keyword in lowered for keyword in USAGE_KEYWORDS):
            return []
    if has_fenced_code(text):
        return []
    return [
        make_finding(
            "readme.usage-not-detected",
            title="No usage example detected",
            detail=(
                "No usage section or example code block was detected; "
                "strangers cannot see how to run the project."
            ),
            path=readme.name,
            evidence=(
                "Checked unfenced lines for usage keywords (usage, "
                "example, demo, ...) and for fenced code blocks; none "
                "found."
            ),
            suggestion=(
                "Add a Usage section with a minimal runnable command or "
                "example."
            ),
        )
    ]


def check_oversized(ctx: ScanContext):
    scan = _scan_readme(ctx)
    if scan is None:
        return None
    readme, _, truncated = scan
    if not truncated:
        return []
    size = readme.stat().st_size
    return [
        make_finding(
            "readme.oversized",
            title="README exceeds the size limit",
            detail=(
                "The README is larger than the read limit; structural and "
                "link checks only analyzed the first "
                f"{README_SIZE_LIMIT} bytes."
            ),
            path=readme.name,
            evidence=(
                f"README is {size} bytes; analysis covered the first "
                f"{README_SIZE_LIMIT} bytes."
            ),
            suggestion=(
                "Trim or split the README; move long content into docs/."
            ),
        )
    ]


# Order mirrors the §2a table in docs/spec/01-architecture-rules.md.
CHECKS = (
    check_no_h1,
    check_install,
    check_usage,
    check_oversized,
)
