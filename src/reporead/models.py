"""Finding and report data model shared by text and JSON renderers.

Field names and value domains mirror docs/spec/report.schema.json
(schema_version 1.0). The schema is the contract; tests assert
consistency in both directions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

SCHEMA_VERSION = "1.0"

SEVERITIES = ("error", "warning", "info")
_FAILING_SEVERITIES = ("error", "warning")

EXIT_OK = 0
EXIT_CHECK_FAILED = 1
EXIT_USAGE = 2


class ModelError(ValueError):
    """Raised when report data violates the frozen model contract."""


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    title: str
    detail: str
    suggestion: str
    path: Optional[str] = None
    evidence: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.rule_id:
            raise ModelError("rule_id must be a non-empty string")
        if self.severity not in SEVERITIES:
            raise ModelError(
                f"severity must be one of {SEVERITIES}, got {self.severity!r}"
            )


@dataclass(frozen=True)
class Summary:
    error_count: int
    warning_count: int
    info_count: int
    passed_rule_count: int
    failed_rule_count: int


def _finding_sort_key(finding: Finding) -> tuple:
    return (
        finding.rule_id,
        finding.path or "",
        finding.title,
        finding.detail,
        finding.evidence or "",
        finding.severity,
    )


@dataclass(frozen=True)
class Report:
    """Immutable check result; findings are stored in a deterministic order.

    Counting semantics (docs/spec/01-architecture-rules.md §2a): a rule
    fails when it produced at least one error or warning finding; a rule
    that only produced info findings (or nothing) counts as passed;
    skipped (not-applicable) rules are counted in neither passed nor
    failed.
    """

    root: str
    findings: tuple[Finding, ...] = ()
    evaluated_rule_count: int = 0
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.root:
            raise ModelError("root must be a non-empty string")
        if self.evaluated_rule_count < 0:
            raise ModelError("evaluated_rule_count must be >= 0")
        object.__setattr__(
            self,
            "findings",
            tuple(sorted(self.findings, key=_finding_sort_key)),
        )

    @property
    def summary(self) -> Summary:
        error_count = sum(1 for f in self.findings if f.severity == "error")
        warning_count = sum(1 for f in self.findings if f.severity == "warning")
        info_count = sum(1 for f in self.findings if f.severity == "info")
        failed = len(
            {f.rule_id for f in self.findings if f.severity in _FAILING_SEVERITIES}
        )
        passed = self.evaluated_rule_count - failed
        if passed < 0:
            raise ModelError(
                f"evaluated_rule_count ({self.evaluated_rule_count}) is smaller "
                f"than the number of failing rules ({failed})"
            )
        return Summary(error_count, warning_count, info_count, passed, failed)


def decide_exit_code(report: Report, *, strict: bool = False) -> int:
    """Frozen exit-code decision table (docs/spec/01-architecture-rules.md §4).

    default: any error -> 1, otherwise 0.
    strict:  any error -> 1; else any warning -> 1; otherwise 0.
    CLI/config/path/output-write failures are usage errors (2) and are
    handled by the CLI, not here.
    """
    if any(f.severity == "error" for f in report.findings):
        return EXIT_CHECK_FAILED
    if strict and any(f.severity == "warning" for f in report.findings):
        return EXIT_CHECK_FAILED
    return EXIT_OK
