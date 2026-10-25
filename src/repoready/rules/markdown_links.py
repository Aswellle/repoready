"""README local link and image checks (offline; docs/spec/01 §5).

MVP subset, enforced by tests and documented in
docs/false-positives.md: inline links/images, full and collapsed
reference links, link reference definitions, autolink-free angle
destinations, fenced-code exclusion, URL decoding, backslash
separators, GitHub-style heading slugs (with -1/-2 duplicates).
Not supported: HTML <a>/<img> tags, bare shorthand references,
nested brackets in labels, setext headings.
"""

from __future__ import annotations

import re
import urllib.parse

from repoready.rules.registry import make_finding

from .context import ScanContext
from .markdown_text import iter_unfenced_lines, read_capped
from .repository_files import find_readme

MARKDOWN_SUFFIXES = (".md", ".markdown")

EXTERNAL_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://|^mailto:", re.IGNORECASE)

INLINE_LINK_RE = re.compile(
    r"!?\[(?P<label>(?:[^\[\]\\]|\\.)*)\]"
    r"\(\s*(?:<(?P<angle>[^>]*)>|(?P<bare>[^)\s]*))"
    r"(?:\s+(?:'[^']*'|\"[^\"]*\"|\([^)]*\)))?\s*\)"
)
REFERENCE_USE_RE = re.compile(
    r"!?\[(?P<label>(?:[^\[\]\\]|\\.)*)\]\[(?P<ref>(?:[^\[\]\\]|\\.)*)\]"
)
REFERENCE_DEF_RE = re.compile(
    r"^[ \t]{0,3}\[(?P<ref>(?:[^\[\]\\]|\\.)*)\]:\s*"
    r"(?:<(?P<angle>[^>]*)>|(?P<bare>\S+))"
    r"(?:\s+(?:'[^']*'|\"[^\"]*\"|\([^)]*\)))?[ \t]*$"
)
ATX_HEADING = re.compile(r"^[ \t]{0,3}(#{1,6})\s+(.*)$")
TRAILING_HASHES = re.compile(r"\s+#+\s*$")


def github_slug(text: str) -> str:
    """GitHub-style heading slug: lowercase, strip punctuation, hyphenate."""
    slug = text.strip().lower()
    slug = re.sub(r"[^\w\- ]", "", slug)
    return slug.replace(" ", "-")


def _readme_scan(ctx: ScanContext):
    readme = find_readme(ctx)
    if readme is None:
        return None
    text, truncated = read_capped(readme)
    return readme, text, truncated


def _collect_reference_defs(text: str) -> dict[str, str]:
    refs: dict[str, str] = {}
    for _, line in iter_unfenced_lines(text):
        match = REFERENCE_DEF_RE.match(line)
        if match:
            key = match.group("ref").strip().lower()
            dest = (
                match.group("angle")
                if match.group("angle") is not None
                else (match.group("bare") or "")
            )
            refs.setdefault(key, dest)
    return refs


def _iter_targets(text: str, refs: dict[str, str]):
    """Yield (line number, label, destination) for every resolvable link."""
    for lineno, line in iter_unfenced_lines(text):
        if REFERENCE_DEF_RE.match(line):
            continue
        for match in INLINE_LINK_RE.finditer(line):
            dest = (
                match.group("angle")
                if match.group("angle") is not None
                else (match.group("bare") or "")
            )
            yield lineno, match.group("label"), dest
        for match in REFERENCE_USE_RE.finditer(line):
            key = (match.group("ref") or match.group("label")).strip().lower()
            if key in refs:
                yield lineno, match.group("label"), refs[key]


def _classify(dest: str) -> tuple[str, tuple[str, str] | None]:
    """Return ('skip'|'external'|'file', (path_part, fragment) | None)."""
    stripped = dest.strip()
    if not stripped:
        return ("skip", None)
    if EXTERNAL_RE.match(stripped):
        return ("external", None)
    path_raw, _, fragment = stripped.partition("#")
    path = urllib.parse.unquote(path_raw.replace("\\", "/"))
    while path.startswith("./"):
        path = path[2:]
    # The README sits at the repository root, so root-relative ("/x")
    # and repo-relative ("x") destinations land in the same place.
    path = path.lstrip("/")
    return ("file", (path, fragment))


def _slug_anchors(text: str) -> set[str]:
    counts: dict[str, int] = {}
    anchors: set[str] = set()
    for _, line in iter_unfenced_lines(text):
        match = ATX_HEADING.match(line)
        if not match:
            continue
        heading = TRAILING_HASHES.sub("", match.group(2))
        slug = github_slug(heading)
        seen = counts.get(slug, 0)
        counts[slug] = seen + 1
        anchors.add(slug if seen == 0 else f"{slug}-{seen}")
    return anchors


def _target_anchors(ctx: ScanContext, path_part: str) -> set[str] | None:
    """Anchors of a linked markdown file, or None when not checkable."""
    candidate = ctx.root / path_part
    if not candidate.is_file():
        return None
    if not candidate.suffix.lower() in MARKDOWN_SUFFIXES:
        return None
    text, truncated = read_capped(candidate)
    if truncated:
        return None
    return _slug_anchors(text)


def check_link_targets(ctx: ScanContext):
    scan = _readme_scan(ctx)
    if scan is None:
        return None
    readme, text, _ = scan
    refs = _collect_reference_defs(text)
    root = ctx.root.resolve()
    findings = []
    for lineno, label, dest in _iter_targets(text, refs):
        kind, payload = _classify(dest)
        if kind != "file" or payload is None:
            continue
        path_part, _ = payload
        if not path_part:
            continue  # pure anchor: checked by check_anchors
        candidate = ctx.root / path_part
        try:
            inside = candidate.resolve(strict=False).is_relative_to(root)
        except OSError:
            inside = False
        if inside and candidate.exists():
            continue
        reason = (
            "resolves outside the repository root"
            if not inside
            else "does not exist in the repository"
        )
        findings.append(
            make_finding(
                "link.target.missing",
                title="README link target not found",
                detail=(
                    f"The relative link '{dest}' does not resolve to an "
                    "existing file or directory inside the repository."
                ),
                path=readme.name,
                evidence=f"line {lineno}: [{label}]({dest}) — {reason}.",
                suggestion=(
                    "Fix the path, create the missing file, or use an "
                    "external https:// link if the target lives outside "
                    "the repository."
                ),
            )
        )
    return findings


def check_anchors(ctx: ScanContext):
    scan = _readme_scan(ctx)
    if scan is None:
        return None
    readme, text, _ = scan
    refs = _collect_reference_defs(text)
    readme_anchors: set[str] | None = None
    target_cache: dict[str, set[str] | None] = {}
    broken: list[str] = []
    for lineno, label, dest in _iter_targets(text, refs):
        kind, payload = _classify(dest)
        if kind != "file" or payload is None:
            continue
        path_part, fragment = payload
        if not fragment:
            continue
        anchor = urllib.parse.unquote(fragment)
        if path_part:
            if path_part not in target_cache:
                target_cache[path_part] = _target_anchors(ctx, path_part)
            anchors = target_cache[path_part]
            display = f"{path_part}#{anchor}"
        else:
            if readme_anchors is None:
                readme_anchors = _slug_anchors(text)
            anchors = readme_anchors
            display = f"#{anchor}"
        if anchors is None:
            continue  # missing/non-markdown/oversized targets: not checkable
        if anchor not in anchors:
            broken.append(f"{display} (line {lineno})")
    if not broken:
        return []
    shown = broken[:5]
    more = len(broken) - len(shown)
    evidence = "anchors not found: " + "; ".join(shown)
    if more > 0:
        evidence += f"; and {more} more"
    return [
        make_finding(
            "link.anchor.not-found",
            title="Some README anchors were not found",
            detail=(
                "Anchor fragments in README links did not match any "
                "heading in the target file (GitHub-style slugs)."
            ),
            path=readme.name,
            evidence=evidence,
            suggestion=(
                "Use GitHub-style anchors (lowercase, spaces as hyphens) "
                "matching the target file's headings."
            ),
        )
    ]


def check_external(ctx: ScanContext):
    scan = _readme_scan(ctx)
    if scan is None:
        return None
    readme, text, _ = scan
    refs = _collect_reference_defs(text)
    count = sum(
        1
        for _, _, dest in _iter_targets(text, refs)
        if _classify(dest)[0] == "external"
    )
    if count == 0:
        return []
    return [
        make_finding(
            "link.external-not-checked",
            title="External links were not checked",
            detail="Offline mode does not verify external URL reachability.",
            path=readme.name,
            evidence=(
                f"{count} external links were found and intentionally "
                "not requested."
            ),
            suggestion=(
                "Verify release-critical external links manually."
            ),
        )
    ]


# Order mirrors the §2a table in docs/spec/01-architecture-rules.md.
CHECKS = (
    check_link_targets,
    check_anchors,
    check_external,
)
