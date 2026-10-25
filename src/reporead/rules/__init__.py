"""Rule registry and check engine.

REGISTRY (rules/registry.py) is the single source of truth for rule
ids, severities and categories; it must stay consistent with the table
in docs/spec/01-architecture-rules.md §2a (enforced by tests).
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from reporead.models import Finding

from . import (
    community_files,
    markdown_links,
    readme_quality,
    release_metadata,
    repository_files,
)
from .context import ScanContext, build_context
from .registry import REGISTRY, RegistryError, RuleSpec, make_finding

# rule_id -> check function. The set of keys must equal the registry
# (enforced by tests); order of CHECKS mirrors the §2a table.
RULE_CHECKS: dict[str, Callable[[ScanContext], list[Finding] | None]] = {
    "repo.readme.missing": repository_files.check_readme,
    "repo.license.missing": repository_files.check_license,
    "repo.manifest.missing": repository_files.check_manifest,
    "repo.gitignore.missing": repository_files.check_gitignore,
    "repo.tests.missing": repository_files.check_tests,
    "repo.ci.missing": repository_files.check_ci,
    "repo.contributing.missing": community_files.check_contributing,
    "repo.security.missing": community_files.check_security,
    "repo.coc.missing": community_files.check_coc,
    "repo.changelog.missing": community_files.check_changelog,
    "repo.templates.issues.missing": community_files.check_issue_templates,
    "repo.templates.pr.missing": community_files.check_pr_template,
    "readme.no-h1": readme_quality.check_no_h1,
    "readme.install-not-detected": readme_quality.check_install,
    "readme.usage-not-detected": readme_quality.check_usage,
    "readme.oversized": readme_quality.check_oversized,
    "link.target.missing": markdown_links.check_link_targets,
    "link.anchor.not-found": markdown_links.check_anchors,
    "link.external-not-checked": markdown_links.check_external,
    "meta.pyproject.required-fields": release_metadata.check_pyproject_fields,
    "meta.packagejson.required-fields": release_metadata.check_packagejson_fields,
    "meta.changelog.current-entry": release_metadata.check_changelog_entry,
}

CHECKS = tuple(RULE_CHECKS[spec.rule_id] for spec in REGISTRY)
_RULE_IDS = {check: rule_id for rule_id, check in RULE_CHECKS.items()}


def run_checks(
    root: Path | ScanContext,
    *,
    disabled_rules: frozenset[str] = frozenset(),
    ignore_paths: tuple[str, ...] = (),
) -> tuple[tuple[Finding, ...], int]:
    """Run every wired check against a repository root (read-only).

    A check returns None when its subject does not apply (currently:
    the README content/link rules without a README, and the metadata
    rules without their subject file). Skipped and disabled rules are
    counted in neither passed nor failed rule counts, per
    docs/spec/01-architecture-rules.md §2a. ignore_paths only applies
    when root is a path (they filter the context snapshot). Returns
    (findings, evaluated_rule_count) with findings in CHECKS order;
    the report model applies the final sort.
    """
    ctx = root if isinstance(root, ScanContext) else build_context(root, ignore_paths)
    findings: list[Finding] = []
    evaluated = 0
    for check in CHECKS:
        if _RULE_IDS[check] in disabled_rules:
            continue
        result = check(ctx)
        if result is None:
            continue
        evaluated += 1
        findings.extend(result)
    return tuple(findings), evaluated


__all__ = [
    "CHECKS",
    "REGISTRY",
    "RULE_CHECKS",
    "RegistryError",
    "RuleSpec",
    "make_finding",
    "run_checks",
]
