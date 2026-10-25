"""Single source of truth for rule ids and severities.

Must stay consistent with the rule table in
docs/spec/01-architecture-rules.md §2a; tests enforce the mapping in
both directions. Rule functions must create findings through
make_finding() so severity can never drift from the registry.
"""

from __future__ import annotations

from dataclasses import dataclass

from reporead.models import Finding


class RegistryError(LookupError):
    """Raised for rule ids that are not in the registry."""


@dataclass(frozen=True)
class RuleSpec:
    rule_id: str
    severity: str
    category: str
    phase: str
    rationale: str


# Order mirrors the §2a table in docs/spec/01-architecture-rules.md.
REGISTRY: tuple[RuleSpec, ...] = (
    RuleSpec("repo.readme.missing", "error", "essential", "1",
             "no README at the repository root (case-insensitive)"),
    RuleSpec("repo.license.missing", "error", "essential", "1",
             "no LICENSE at the repository root"),
    RuleSpec("repo.manifest.missing", "error", "essential", "1",
             "no known dependency/project manifest"),
    RuleSpec("repo.gitignore.missing", "warning", "essential", "1",
             "no .gitignore"),
    RuleSpec("repo.tests.missing", "warning", "essential", "1",
             "no test directory or test configuration"),
    RuleSpec("repo.ci.missing", "warning", "essential", "1",
             "no CI workflow"),
    RuleSpec("repo.contributing.missing", "warning", "community", "1",
             "no CONTRIBUTING"),
    RuleSpec("repo.security.missing", "warning", "community", "1",
             "no SECURITY"),
    RuleSpec("repo.coc.missing", "warning", "community", "1",
             "no CODE_OF_CONDUCT"),
    RuleSpec("repo.changelog.missing", "warning", "community", "1",
             "no CHANGELOG"),
    RuleSpec("repo.templates.issues.missing", "info", "community", "1",
             "no issue templates"),
    RuleSpec("repo.templates.pr.missing", "info", "community", "1",
             "no pull request template"),
    RuleSpec("readme.no-h1", "warning", "readme", "2",
             "no H1 heading detected in README"),
    RuleSpec("readme.install-not-detected", "warning", "readme", "2",
             "no install/run instructions detected in README"),
    RuleSpec("readme.usage-not-detected", "warning", "readme", "2",
             "no usage example detected in README"),
    RuleSpec("link.target.missing", "error", "links", "2",
             "README local link/image target does not exist"),
    RuleSpec("link.anchor.not-found", "info", "links", "2",
             "README anchor not found (informational)"),
    RuleSpec("link.external-not-checked", "info", "links", "2",
             "external links are listed, not checked (offline)"),
    RuleSpec("meta.pyproject.required-fields", "warning", "metadata", "2.5",
             "pyproject.toml required fields missing"),
    RuleSpec("meta.packagejson.required-fields", "warning", "metadata", "2.5",
             "package.json required fields missing"),
    RuleSpec("meta.changelog.current-entry", "info", "metadata", "2.5",
             "no current entry in CHANGELOG"),
)

_BY_ID = {spec.rule_id: spec for spec in REGISTRY}


def get_spec(rule_id: str) -> RuleSpec:
    """Return the registry entry for rule_id or raise RegistryError."""
    try:
        return _BY_ID[rule_id]
    except KeyError:
        raise RegistryError(f"unregistered rule_id: {rule_id!r}") from None


def make_finding(
    rule_id: str,
    *,
    title: str,
    detail: str,
    suggestion: str,
    path: str | None = None,
    evidence: str | None = None,
) -> Finding:
    """Build a Finding with the severity frozen by the registry."""
    spec = get_spec(rule_id)
    return Finding(
        rule_id=rule_id,
        severity=spec.severity,
        title=title,
        detail=detail,
        suggestion=suggestion,
        path=path,
        evidence=evidence,
    )
