"""Deterministic JSON rendering of Report (docs/spec/report.schema.json)."""

from __future__ import annotations

import json

from .models import Report


def render_json(report: Report) -> str:
    """Render the report as schema-conformant JSON with a trailing newline.

    Deterministic: findings are pre-sorted in the model and object keys
    are sorted, so identical reports render to identical bytes on every
    platform. ensure_ascii=True keeps the output writable on any console
    encoding.
    """
    s = report.summary
    payload = {
        "schema_version": report.schema_version,
        "root": report.root,
        "summary": {
            "error_count": s.error_count,
            "warning_count": s.warning_count,
            "info_count": s.info_count,
            "passed_rule_count": s.passed_rule_count,
            "failed_rule_count": s.failed_rule_count,
        },
        "findings": [
            {
                "rule_id": f.rule_id,
                "severity": f.severity,
                "title": f.title,
                "detail": f.detail,
                "path": f.path,
                "evidence": f.evidence,
                "suggestion": f.suggestion,
            }
            for f in report.findings
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
