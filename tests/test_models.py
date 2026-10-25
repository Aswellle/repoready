"""Unit tests for the frozen report model and exit-code decision table."""

import unittest

from repoready.models import (
    EXIT_CHECK_FAILED,
    EXIT_OK,
    Finding,
    ModelError,
    Report,
    decide_exit_code,
)


def _finding(rule_id: str = "r.a", severity: str = "info", **kwargs) -> Finding:
    return Finding(
        rule_id=rule_id,
        severity=severity,
        title="t",
        detail="d",
        suggestion="s",
        **kwargs,
    )


class FindingTests(unittest.TestCase):
    def test_rejects_unknown_severity(self):
        with self.assertRaises(ModelError):
            _finding(severity="critical")

    def test_rejects_empty_rule_id(self):
        with self.assertRaises(ModelError):
            _finding(rule_id="")

    def test_accepts_schema_severities_and_null_path(self):
        for severity in ("error", "warning", "info"):
            f = _finding(severity=severity)
            self.assertIsNone(f.path)


class SummaryTests(unittest.TestCase):
    def test_zero_rules_zero_findings(self):
        s = Report(root=".", findings=(), evaluated_rule_count=0).summary
        self.assertEqual(
            (s.error_count, s.warning_count, s.info_count), (0, 0, 0)
        )
        self.assertEqual((s.passed_rule_count, s.failed_rule_count), (0, 0))

    def test_info_only_rule_counts_as_passed(self):
        report = Report(
            root=".",
            findings=(_finding(rule_id="x.y", severity="info"),),
            evaluated_rule_count=2,
        )
        s = report.summary
        self.assertEqual((s.failed_rule_count, s.passed_rule_count), (0, 2))

    def test_error_and_warning_fail_their_rule_once(self):
        report = Report(
            root=".",
            findings=(
                _finding(rule_id="a.b", severity="error"),
                _finding(rule_id="a.b", severity="warning"),
                _finding(rule_id="c.d", severity="info"),
            ),
            evaluated_rule_count=3,
        )
        s = report.summary
        self.assertEqual((s.error_count, s.warning_count, s.info_count), (1, 1, 1))
        self.assertEqual((s.failed_rule_count, s.passed_rule_count), (1, 2))

    def test_evaluated_smaller_than_failed_raises(self):
        report = Report(
            root=".",
            findings=(_finding(rule_id="a.b", severity="error"),),
            evaluated_rule_count=0,
        )
        with self.assertRaises(ModelError):
            report.summary


class SortingTests(unittest.TestCase):
    def test_findings_sorted_deterministically(self):
        f1 = _finding(rule_id="b.b")
        f2 = _finding(rule_id="a.a")
        r1 = Report(root=".", findings=(f1, f2))
        r2 = Report(root=".", findings=(f2, f1))
        self.assertEqual(r1.findings, r2.findings)
        self.assertEqual([f.rule_id for f in r1.findings], ["a.a", "b.b"])

    def test_missing_path_sorts_before_paths(self):
        f_none = _finding(rule_id="a.a", path=None)
        f_path = _finding(rule_id="a.a", path="z.md")
        report = Report(root=".", findings=(f_path, f_none))
        self.assertIs(report.findings[0], f_none)

    def test_negative_evaluated_count_rejected(self):
        with self.assertRaises(ModelError):
            Report(root=".", findings=(), evaluated_rule_count=-1)


class ExitCodeDecisionTests(unittest.TestCase):
    """docs/spec/01-architecture-rules.md §4 decision table."""

    def test_empty_report_passes_default_and_strict(self):
        report = Report(root=".", findings=(), evaluated_rule_count=0)
        self.assertEqual(decide_exit_code(report), EXIT_OK)
        self.assertEqual(decide_exit_code(report, strict=True), EXIT_OK)

    def test_warning_only_fails_strict_only(self):
        report = Report(
            root=".",
            findings=(_finding(severity="warning"),),
            evaluated_rule_count=1,
        )
        self.assertEqual(decide_exit_code(report), EXIT_OK)
        self.assertEqual(decide_exit_code(report, strict=True), EXIT_CHECK_FAILED)

    def test_error_fails_default_and_strict(self):
        report = Report(
            root=".",
            findings=(
                _finding(rule_id="e.f", severity="error"),
                _finding(rule_id="g.h", severity="warning"),
            ),
            evaluated_rule_count=2,
        )
        self.assertEqual(decide_exit_code(report), EXIT_CHECK_FAILED)
        self.assertEqual(decide_exit_code(report, strict=True), EXIT_CHECK_FAILED)

    def test_info_only_never_fails(self):
        report = Report(
            root=".",
            findings=(_finding(severity="info"),),
            evaluated_rule_count=1,
        )
        self.assertEqual(decide_exit_code(report), EXIT_OK)
        self.assertEqual(decide_exit_code(report, strict=True), EXIT_OK)


if __name__ == "__main__":
    unittest.main()
