"""Release metadata consistency checks (docs/spec/02, metadata rules).

Existence and format only: a missing field is reported, the semantic
correctness of what is there is never judged. Each check applies only
when its subject file exists; otherwise it returns None (skipped).

Neighborhood note (verified 2026-10-26 via PyPI): pyroma 5.0.1 rates
packaging best practices with deeper semantics, check-manifest 0.51
covers sdist file completeness. These rules stay dependency-free and
existence-only by design.
"""

from __future__ import annotations

import json
import re
import tomllib

from repoready.rules.registry import make_finding

from .context import ScanContext
from .markdown_text import (
    README_SIZE_LIMIT,
    iter_headings,
    read_capped,
)

# Frozen required [project] fields (docs/spec review §5 D2): name,
# version, description, readme, plus license or license-files.
PYPROJECT_FIELDS = ("name", "version", "description", "readme")
PACKAGEJSON_FIELDS = ("name", "version", "description", "license")

CHANGELOG_VERSION_TEXT = re.compile(
    r"\b(?:unreleased|v?\d+\.\d+(?:\.\d+)?)\b", re.IGNORECASE
)


def _truncation_finding(rule_id: str, path: str) -> dict:
    return make_finding(
        rule_id,
        title=f"{path} exceeds the read limit",
        detail=(
            f"The file is larger than the {README_SIZE_LIMIT} byte read "
            "limit; field checks were skipped instead of reading it all."
        ),
        path=path,
        evidence=f"File size exceeds {README_SIZE_LIMIT} bytes.",
        suggestion="Keep packaging metadata small enough to review.",
    )


def check_pyproject_fields(ctx: ScanContext):
    path = ctx.root / "pyproject.toml"
    if not path.is_file():
        return None
    text, truncated = read_capped(path)
    if truncated:
        return [_truncation_finding("meta.pyproject.required-fields", "pyproject.toml")]
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        summary = str(exc).splitlines()[0][:200]
        return [
            make_finding(
                "meta.pyproject.required-fields",
                title="pyproject.toml is not valid TOML",
                detail=(
                    "pyproject.toml could not be parsed; packaging tools "
                    "will fail on it."
                ),
                path="pyproject.toml",
                evidence=f"TOML parse error: {summary}",
                suggestion="Fix the TOML syntax error reported in the evidence.",
            )
        ]
    project = data.get("project")
    if not isinstance(project, dict):
        return [
            make_finding(
                "meta.pyproject.required-fields",
                title="No [project] table in pyproject.toml",
                detail=(
                    "pyproject.toml has no [project] table, so core "
                    "packaging metadata is not declared (PEP 621)."
                ),
                path="pyproject.toml",
                evidence="Checked pyproject.toml for a [project] table; none found.",
                suggestion="Add a [project] table with at least name and version.",
            )
        ]
    dynamic = project.get("dynamic")
    dynamic_fields = set(dynamic) if isinstance(dynamic, list) else set()
    findings = []
    for field in PYPROJECT_FIELDS:
        if field in project or field in dynamic_fields:
            continue
        findings.append(
            make_finding(
                "meta.pyproject.required-fields",
                title=f"pyproject.toml missing '{field}'",
                detail=(
                    f"The [project] table has no '{field}' field; release "
                    "metadata will be incomplete."
                ),
                path="pyproject.toml",
                evidence=(
                    f"Checked [project] for '{field}'; neither present nor "
                    "listed in dynamic."
                ),
                suggestion=(
                    f"Add '{field}' to the [project] table (or list it in "
                    "dynamic if it is generated elsewhere)."
                ),
            )
        )
    if (
        "license" not in project
        and "license-files" not in project
        and "license" not in dynamic_fields
    ):
        findings.append(
            make_finding(
                "meta.pyproject.required-fields",
                title="pyproject.toml missing 'license'",
                detail=(
                    "The [project] table declares neither 'license' nor "
                    "'license-files'; the released package shows no license."
                ),
                path="pyproject.toml",
                evidence=(
                    "Checked [project] for 'license' or 'license-files'; "
                    "neither present ('license' also not in dynamic)."
                ),
                suggestion=(
                    "Add 'license' or 'license-files' to the [project] table."
                ),
            )
        )
    return findings


def check_packagejson_fields(ctx: ScanContext):
    path = ctx.root / "package.json"
    if not path.is_file():
        return None
    text, truncated = read_capped(path)
    if truncated:
        return [_truncation_finding("meta.packagejson.required-fields", "package.json")]
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        summary = str(exc).splitlines()[0][:200]
        return [
            make_finding(
                "meta.packagejson.required-fields",
                title="package.json is not valid JSON",
                detail="package.json could not be parsed; npm will fail on it.",
                path="package.json",
                evidence=f"JSON parse error: {summary}",
                suggestion="Fix the JSON syntax error reported in the evidence.",
            )
        ]
    if not isinstance(data, dict):
        return [
            make_finding(
                "meta.packagejson.required-fields",
                title="package.json root is not a JSON object",
                detail="package.json must contain a JSON object at the top level.",
                path="package.json",
                evidence="The top-level JSON value is not an object.",
                suggestion="Restructure package.json so its root is an object.",
            )
        ]
    findings = []
    for field in PACKAGEJSON_FIELDS:
        if field in data:
            continue
        findings.append(
            make_finding(
                "meta.packagejson.required-fields",
                title=f"package.json missing '{field}'",
                detail=(
                    f"package.json has no '{field}' field; npm metadata "
                    "will be incomplete."
                ),
                path="package.json",
                evidence=f"Checked package.json for '{field}'; not present.",
                suggestion=f"Add '{field}' to package.json.",
            )
        )
    return findings


def _changelog_path(ctx: ScanContext):
    for name in sorted(ctx.root_file_names):
        if name.lower() == "changelog.md":
            return ctx.root / name
    for entry in ctx.docs_entries:
        if not entry.is_dir and entry.name.lower() == "releases.md":
            return ctx.root / "docs" / entry.name
    return None


def check_changelog_entry(ctx: ScanContext):
    path = _changelog_path(ctx)
    if path is None:
        return None
    text, _ = read_capped(path)
    for _, _level, heading in iter_headings(text):
        if CHANGELOG_VERSION_TEXT.search(heading):
            return []
    return [
        make_finding(
            "meta.changelog.current-entry",
            title="No version entry detected in CHANGELOG",
            detail=(
                "No 'Unreleased' or version-number heading was detected; "
                "user-visible changes may not be recorded per release."
            ),
            path=str(path.relative_to(ctx.root)).replace("\\", "/"),
            evidence=(
                "Checked headings for 'Unreleased' or a version number "
                "like 0.1.0; none found."
            ),
            suggestion=(
                "Add an '## Unreleased' or '## 0.1.1' section describing "
                "user-visible changes."
            ),
        )
    ]


# Order mirrors the §2a table in docs/spec/01-architecture-rules.md.
CHECKS = (
    check_pyproject_fields,
    check_packagejson_fields,
    check_changelog_entry,
)
