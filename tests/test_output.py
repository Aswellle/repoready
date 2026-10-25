"""Renderer determinism and schema-conformance tests (text + JSON)."""

import json
import unittest
from pathlib import Path

from repoready import report_json, report_text
from repoready.models import Finding, Report

SCHEMA_PATH = (
    Path(__file__).resolve().parents[1] / "docs" / "spec" / "report.schema.json"
)


def _sample_report() -> Report:
    return Report(
        root="/repo",
        findings=(
            Finding(
                rule_id="repo.license.missing",
                severity="error",
                title="LICENSE file not found",
                detail="No LICENSE was found.",
                suggestion="Add a LICENSE file.",
                path="LICENSE",
                evidence="No license file matched known names.",
            ),
            Finding(
                rule_id="link.external-not-checked",
                severity="info",
                title="External links were not checked",
                detail="Offline mode does not verify external URLs.",
                suggestion="Verify manually if release-critical.",
                path="README.md",
                evidence="3 external links found.",
            ),
            Finding(
                rule_id="readme.install-not-detected",
                severity="warning",
                title="Install instructions not detected",
                detail="No install section detected.",
                suggestion="Add an installation section.",
                path="README.md",
            ),
        ),
        evaluated_rule_count=21,
    )


class SchemaConformanceTests(unittest.TestCase):
    def setUp(self):
        self.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_rendered_json_matches_schema_structure(self):
        rendered = json.loads(report_json.render_json(_sample_report()))
        self.assertEqual(set(rendered), set(self.schema["properties"]))
        self.assertEqual(
            rendered["schema_version"],
            self.schema["properties"]["schema_version"]["const"],
        )
        self.assertEqual(
            set(rendered["summary"]),
            set(self.schema["properties"]["summary"]["properties"]),
        )
        item_schema = self.schema["properties"]["findings"]["items"]
        for finding in rendered["findings"]:
            self.assertEqual(set(finding), set(item_schema["properties"]))
            self.assertIn(
                finding["severity"], item_schema["properties"]["severity"]["enum"]
            )


class DeterminismTests(unittest.TestCase):
    def test_json_render_is_byte_stable(self):
        first = report_json.render_json(_sample_report())
        second = report_json.render_json(_sample_report())
        self.assertEqual(first, second)
        self.assertTrue(first.endswith("\n"))

    def test_text_render_is_byte_stable(self):
        first = report_text.render_text(_sample_report())
        second = report_text.render_text(_sample_report())
        self.assertEqual(first, second)

    def test_no_ansi_escape_codes(self):
        out = report_text.render_text(_sample_report()) + report_json.render_json(
            _sample_report()
        )
        self.assertNotIn("\x1b", out)

    def test_findings_ordered_by_rule_id(self):
        payload = json.loads(report_json.render_json(_sample_report()))
        self.assertEqual(
            [f["rule_id"] for f in payload["findings"]],
            [
                "link.external-not-checked",
                "readme.install-not-detected",
                "repo.license.missing",
            ],
        )

    def test_summary_matches_example_contract(self):
        payload = json.loads(report_json.render_json(_sample_report()))
        self.assertEqual(
            payload["summary"],
            {
                "error_count": 1,
                "warning_count": 1,
                "info_count": 1,
                "passed_rule_count": 19,
                "failed_rule_count": 2,
            },
        )


class TextRenderingTests(unittest.TestCase):
    def test_text_lists_rule_ids_and_severities(self):
        text = report_text.render_text(_sample_report())
        self.assertIn("[error] repo.license.missing", text)
        self.assertIn("[warning] readme.install-not-detected", text)
        self.assertIn("[info] link.external-not-checked", text)
        self.assertIn("path: README.md", text)
        self.assertIn("suggestion:", text)

    def test_text_states_limits_honestly(self):
        text = report_text.render_text(_sample_report())
        self.assertIn("file existence does not imply", text)

    def test_empty_report_has_no_findings_line(self):
        text = report_text.render_text(
            Report(root="/repo", findings=(), evaluated_rule_count=0)
        )
        self.assertIn("no findings", text)
        self.assertIn("rules evaluated: 0 (0 passed, 0 failed)", text)


if __name__ == "__main__":
    unittest.main()
