"""Rule registry and check engine.

REGISTRY (rules/registry.py) is the single source of truth for rule
ids, severities and categories; it must stay consistent with the table
in docs/spec/01-architecture-rules.md §2a (enforced by tests).
"""

from __future__ import annotations

from pathlib import Path

from reporead.models import Finding

from . import community_files, markdown_links, readme_quality, repository_files
from .context import ScanContext, build_context
from .registry import REGISTRY, RegistryError, RuleSpec, make_finding

# Order mirrors the §2a table; findings get the final deterministic
# sort in the report model.
CHECKS = (
    repository_files.CHECKS
    + community_files.CHECKS
    + readme_quality.CHECKS
    + markdown_links.CHECKS
)


def run_checks(root: Path | ScanContext) -> tuple[tuple[Finding, ...], int]:
    """Run every wired check against a repository root (read-only).

    A check returns None when its subject does not apply (currently:
    the README content/link rules without a README). Skipped rules are
    counted in neither passed nor failed rule counts, per
    docs/spec/01-architecture-rules.md §2a. Returns
    (findings, evaluated_rule_count) with findings in CHECKS order;
    the report model applies the final sort.
    """
    ctx = root if isinstance(root, ScanContext) else build_context(root)
    findings: list[Finding] = []
    evaluated = 0
    for check in CHECKS:
        result = check(ctx)
        if result is None:
            continue
        evaluated += 1
        findings.extend(result)
    return tuple(findings), evaluated


__all__ = [
    "CHECKS",
    "REGISTRY",
    "RegistryError",
    "RuleSpec",
    "make_finding",
    "run_checks",
]
