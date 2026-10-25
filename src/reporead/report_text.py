"""Deterministic plain-text rendering of Report (no colors, no ANSI)."""

from __future__ import annotations

from . import __version__
from .models import Report


def render_text(report: Report) -> str:
    lines = [
        f"reporead {__version__} - repository readiness check (RepoReady internal dev build)",
        f"root: {report.root}",
    ]
    s = report.summary
    lines.append(
        f"rules evaluated: {report.evaluated_rule_count} "
        f"({s.passed_rule_count} passed, {s.failed_rule_count} failed)"
    )
    lines.append(
        f"findings: {s.error_count} error(s), {s.warning_count} warning(s), "
        f"{s.info_count} info"
    )
    if not report.findings:
        lines.append("no findings")
    else:
        lines.append("findings:")
        for f in report.findings:
            lines.append(f"[{f.severity}] {f.rule_id}: {f.title}")
            if f.path is not None:
                lines.append(f"  path: {f.path}")
            lines.append(f"  detail: {f.detail}")
            if f.evidence is not None:
                lines.append(f"  evidence: {f.evidence}")
            lines.append(f"  suggestion: {f.suggestion}")
    lines.append(
        "note: structural checks only; file existence does not imply "
        "code quality or security."
    )
    return "\n".join(lines) + "\n"
