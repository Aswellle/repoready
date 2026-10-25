"""Rule registry and check engine.

REGISTRY (rules/registry.py) is the single source of truth for rule
ids, severities and categories; it must stay consistent with the table
in docs/spec/01-architecture-rules.md §2a (enforced by tests).
"""

from __future__ import annotations

from pathlib import Path

from reporead.models import Finding

from . import community_files, repository_files
from .context import ScanContext, build_context
from .registry import REGISTRY, RegistryError, RuleSpec, make_finding

# Order mirrors the §2a table; findings get the final deterministic
# sort in the report model.
CHECKS = repository_files.CHECKS + community_files.CHECKS


def run_checks(root: Path | ScanContext) -> tuple[tuple[Finding, ...], int]:
    """Run every wired check against a repository root (read-only).

    Returns (findings, evaluated_rule_count). Findings come back in
    CHECKS order; the report model applies the final sort.
    """
    ctx = root if isinstance(root, ScanContext) else build_context(root)
    findings: list[Finding] = []
    for check in CHECKS:
        findings.extend(check(ctx))
    return tuple(findings), len(CHECKS)


__all__ = [
    "CHECKS",
    "REGISTRY",
    "RegistryError",
    "RuleSpec",
    "make_finding",
    "run_checks",
]
