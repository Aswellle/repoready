"""CLI-level tests: exit codes, output formats, --output behavior."""

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

import fixture_builders as fb
from reporead import __version__
from reporead.cli import build_parser, main

FIXTURES = Path(__file__).resolve().parent / "fixtures"
GOLDEN_COMPLETE = FIXTURES / "golden_complete_repo"
GOLDEN_EMPTY = FIXTURES / "golden_empty_repo"
GOLDEN_EMPTY_REPORT = FIXTURES / "golden_empty_report.json"


def _run(argv):
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = main(argv)
    return code, stdout.getvalue(), stderr.getvalue()


class ParserTests(unittest.TestCase):
    def test_version_exits_zero(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            with self.assertRaises(SystemExit) as ctx:
                main(["--version"])
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn(__version__, stdout.getvalue())

    def test_missing_subcommand_exits_two(self):
        with self.assertRaises(SystemExit) as ctx:
            main([])
        self.assertEqual(ctx.exception.code, 2)

    def test_unknown_flag_exits_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit) as ctx:
                main(["check", "--bogus", tmp])
            self.assertEqual(ctx.exception.code, 2)

    def test_invalid_format_choice_exits_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit) as ctx:
                main(["check", tmp, "--format", "xml"])
            self.assertEqual(ctx.exception.code, 2)

    def test_parser_builds_with_expected_flags(self):
        parser = build_parser()
        args = parser.parse_args(["check", "some/path", "--format", "json",
                                  "--strict", "--output", "out.json"])
        self.assertEqual(args.path, "some/path")
        self.assertEqual(args.format, "json")
        self.assertTrue(args.strict)
        self.assertEqual(str(args.output), "out.json")


class CheckExitCodeTests(unittest.TestCase):
    def test_empty_dir_fails_with_missing_readme_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, _ = _run(["check", tmp])
            self.assertEqual(code, 1)
            self.assertIn("rules evaluated: 12", out)
            self.assertIn("[error] repo.readme.missing", out)
            self.assertNotIn("no findings", out)

    def test_empty_dir_json_summary_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, _ = _run(["check", tmp, "--format", "json"])
            self.assertEqual(code, 1)
            payload = json.loads(out)
            self.assertEqual(payload["schema_version"], "1.0")
            self.assertEqual(len(payload["findings"]), 12)
            self.assertEqual(
                payload["summary"],
                {
                    "error_count": 3,
                    "warning_count": 7,
                    "info_count": 2,
                    "passed_rule_count": 2,
                    "failed_rule_count": 10,
                },
            )

    def test_strict_same_as_default_when_errors_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, _ = _run(["check", tmp, "--strict"])
            self.assertEqual(code, 1)

    def test_nonexistent_path_exits_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = str(Path(tmp) / "no-such-dir")
            code, _, err = _run(["check", missing])
            self.assertEqual(code, 2)
            self.assertIn("error", err)

    def test_file_as_root_exits_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "file.txt"
            target.write_text("x", encoding="utf-8")
            code, _, err = _run(["check", str(target)])
            self.assertEqual(code, 2)
            self.assertIn("not a directory", err)

    def test_default_path_is_current_directory(self):
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            try:
                code, _, _ = _run(["check"])
            finally:
                os.chdir(original_cwd)
            self.assertEqual(code, 1)

    def test_scan_does_not_execute_target_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fb.make_repo_with_never_execute_payload(Path(tmp))
            code, _, _ = _run(["check", str(root)])
            self.assertEqual(code, 1)
            self.assertFalse((root / "EXECUTED_MARKER").exists())


class GoldenFixtureTests(unittest.TestCase):
    def test_complete_repo_passes_all_applicable_rules(self):
        code, out, _ = _run(["check", str(GOLDEN_COMPLETE)])
        self.assertEqual(code, 0)
        self.assertIn("rules evaluated: 21 (21 passed, 0 failed)", out)
        self.assertIn("no findings", out)

    def test_complete_repo_json_exit_zero(self):
        code, out, _ = _run(["check", str(GOLDEN_COMPLETE), "--format", "json"])
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["findings"], [])
        self.assertEqual(payload["summary"]["failed_rule_count"], 0)

    def test_empty_repo_exits_one_default_and_strict(self):
        for extra in ([], ["--strict"]):
            with self.subTest(flags=extra):
                code, _, _ = _run(["check", str(GOLDEN_EMPTY), *extra])
                self.assertEqual(code, 1)

    def test_empty_repo_matches_golden_snapshot(self):
        code, out, _ = _run(["check", str(GOLDEN_EMPTY), "--format", "json"])
        self.assertEqual(code, 1)
        payload = json.loads(out)
        golden = json.loads(GOLDEN_EMPTY_REPORT.read_text(encoding="utf-8"))
        self.assertEqual(payload["summary"], golden["summary"])
        self.assertEqual(payload["findings"], golden["findings"])

    def test_findings_sorted_by_rule_id(self):
        _, out, _ = _run(["check", str(GOLDEN_EMPTY), "--format", "json"])
        payload = json.loads(out)
        rule_ids = [f["rule_id"] for f in payload["findings"]]
        self.assertEqual(rule_ids, sorted(rule_ids))

    def test_broken_readme_link_fails_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text(
                "# T\n\nSee [guide](missing.md).\n", encoding="utf-8"
            )
            code, out, _ = _run(["check", str(root)])
            self.assertEqual(code, 1)
            self.assertIn("[error] link.target.missing", out)


class ConfigCliTests(unittest.TestCase):
    def _config(self, tmp, text: str) -> str:
        path = Path(tmp) / "reporead.toml"
        path.write_text(text, encoding="utf-8")
        return str(path)

    def test_missing_config_file_exits_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "no-such.toml"
            code, _, err = _run(["check", tmp, "--config", str(missing)])
            self.assertEqual(code, 2)
            self.assertIn("cannot read config", err)

    def test_unknown_config_key_exits_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = self._config(tmp, "[thresholds]\nmin = 80\n")
            code, _, err = _run(["check", tmp, "--config", config])
            self.assertEqual(code, 2)
            self.assertIn("thresholds", err)

    def test_unknown_rule_id_in_config_exits_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = self._config(tmp, '[rules]\ndisable = ["not.a.rule"]\n')
            code, _, err = _run(["check", tmp, "--config", config])
            self.assertEqual(code, 2)
            self.assertIn("not.a.rule", err)

    def test_disable_takes_effect_on_golden_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = self._config(
                tmp,
                "[rules]\n"
                'disable = ["repo.templates.issues.missing", '
                '"repo.templates.pr.missing"]\n',
            )
            code, out, _ = _run(["check", str(GOLDEN_EMPTY), "--config", config])
            self.assertEqual(code, 1)
            self.assertIn("rules evaluated: 10", out)
            self.assertNotIn("repo.templates.issues.missing", out)

    def test_ignore_makes_file_invisible(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = self._config(tmp, '[ignore]\npaths = ["README.md"]\n')
            code, out, _ = _run(["check", str(GOLDEN_COMPLETE), "--config", config])
            self.assertEqual(code, 1)
            self.assertIn("[error] repo.readme.missing", out)


class OutputFileTests(unittest.TestCase):
    def test_output_writes_report_file_and_keeps_stdout_empty(self):
        report_path = GOLDEN_COMPLETE.parent / "report.json"
        self.addCleanup(lambda: report_path.unlink(missing_ok=True))
        code, out, _ = _run(
            ["check", str(GOLDEN_COMPLETE), "--format", "json",
             "--output", str(report_path)]
        )
        self.assertEqual(code, 0)
        self.assertEqual(out, "")
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], "1.0")

    def test_output_missing_parent_directory_exits_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "missing-dir" / "report.json"
            code, _, err = _run(
                ["check", tmp, "--format", "json", "--output", str(report_path)]
            )
            self.assertEqual(code, 2)
            self.assertIn(str(report_path), err)

    def test_output_text_report_written_with_newline(self):
        report_path = GOLDEN_COMPLETE.parent / "report.txt"
        self.addCleanup(lambda: report_path.unlink(missing_ok=True))
        code, _, _ = _run(["check", str(GOLDEN_COMPLETE), "--output", str(report_path)])
        self.assertEqual(code, 0)
        content = report_path.read_text(encoding="utf-8")
        self.assertTrue(content.endswith("\n"))
        self.assertIn("no findings", content)


class WindowsStylePathTests(unittest.TestCase):
    def test_check_on_paths_with_spaces_and_cjk_runs_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fb.make_repo_with_windows_style_paths(Path(tmp))
            code, out, _ = _run(["check", str(root)])
            self.assertEqual(code, 1)
            self.assertIn("[error] repo.readme.missing", out)

    def test_check_on_missing_license_fixture_reports_license_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fb.make_repo_missing_license(Path(tmp))
            code, out, _ = _run(["check", str(root), "--format", "json"])
            self.assertEqual(code, 1)
            payload = json.loads(out)
            rule_ids = [f["rule_id"] for f in payload["findings"]]
            self.assertIn("repo.license.missing", rule_ids)
            self.assertNotIn("repo.manifest.missing", rule_ids)
            self.assertNotIn("repo.readme.missing", rule_ids)
            self.assertEqual(payload["summary"]["error_count"], 1)


if __name__ == "__main__":
    unittest.main()
