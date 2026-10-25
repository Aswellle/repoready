"""Tests for README structure heuristics (pass/fail/skip/edges)."""

import tempfile
import unittest
from pathlib import Path

from repoready.rules.context import build_context
from repoready.rules.markdown_text import README_SIZE_LIMIT
from repoready.rules import readme_quality as rq


def _run(check, files: dict[str, str | bytes]):
    """Build a temp repo from {name: content} and run one check."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for name, content in files.items():
            target = root / name
            if isinstance(content, bytes):
                target.write_bytes(content)
            else:
                target.write_text(content, encoding="utf-8")
        findings = check(build_context(root))
    return findings


class SkipTests(unittest.TestCase):
    def test_no_readme_skips_all_content_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = build_context(Path(tmp))
            for check in rq.CHECKS:
                self.assertIsNone(check(ctx), msg=check.__name__)


class NoH1Tests(unittest.TestCase):
    def test_passes_with_h1(self):
        self.assertEqual(_run(rq.check_no_h1, {"README.md": "# Title\n"}), [])

    def test_passes_with_indented_h1(self):
        self.assertEqual(_run(rq.check_no_h1, {"README.md": "  # Title\n"}), [])

    def test_fails_with_only_h2(self):
        findings = _run(rq.check_no_h1, {"README.md": "## Sub\n"})
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].rule_id, "readme.no-h1")
        self.assertEqual(findings[0].path, "README.md")

    def test_heading_inside_fence_is_ignored(self):
        files = {"README.md": "```text\n# not a heading\n```\nbody\n"}
        self.assertEqual(len(_run(rq.check_no_h1, files)), 1)

    def test_four_space_heading_is_code_block_not_h1(self):
        findings = _run(rq.check_no_h1, {"README.md": "    # Title\n"})
        self.assertEqual(len(findings), 1)

    def test_setext_heading_not_supported(self):
        findings = _run(rq.check_no_h1, {"README.md": "Title\n=====\n"})
        self.assertEqual(len(findings), 1)


class InstallTests(unittest.TestCase):
    def test_passes_with_install_heading(self):
        files = {"README.md": "# T\n\n## Install\n\npip install demo\n"}
        self.assertEqual(_run(rq.check_install, files), [])

    def test_passes_with_keyword_in_body(self):
        files = {"README.md": "# T\n\nRun `pip install demo` first.\n"}
        self.assertEqual(_run(rq.check_install, files), [])

    def test_case_insensitive(self):
        files = {"README.md": "# T\n\n## INSTALLATION\n"}
        self.assertEqual(_run(rq.check_install, files), [])

    def test_fails_without_signal(self):
        files = {"README.md": "# T\n\nJust a description.\n"}
        findings = _run(rq.check_install, files)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].rule_id, "readme.install-not-detected")

    def test_keyword_inside_fence_does_not_count(self):
        files = {"README.md": "# T\n\n```\npip install demo\n```\n"}
        self.assertEqual(len(_run(rq.check_install, files)), 1)


class UsageTests(unittest.TestCase):
    def test_passes_with_usage_heading(self):
        files = {"README.md": "# T\n\n## Usage\n\ndemo --help\n"}
        self.assertEqual(_run(rq.check_usage, files), [])

    def test_passes_with_fenced_code_block_alone(self):
        files = {"README.md": "# T\n\n```\ndemo --help\n```\n"}
        self.assertEqual(_run(rq.check_usage, files), [])

    def test_fails_without_signal(self):
        files = {"README.md": "# T\n\nNothing here.\n"}
        findings = _run(rq.check_usage, files)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].rule_id, "readme.usage-not-detected")


class OversizedTests(unittest.TestCase):
    def test_fails_when_over_limit(self):
        files = {"README.md": "a" * (README_SIZE_LIMIT + 1)}
        findings = _run(rq.check_oversized, files)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].rule_id, "readme.oversized")
        self.assertIn(str(README_SIZE_LIMIT), findings[0].evidence)

    def test_passes_at_exactly_the_limit(self):
        files = {"README.md": "a" * README_SIZE_LIMIT}
        self.assertEqual(_run(rq.check_oversized, files), [])

    def test_content_checks_still_work_on_truncated_readme(self):
        files = {"README.md": "# Title\n" + "a" * (README_SIZE_LIMIT + 1)}
        self.assertEqual(_run(rq.check_no_h1, files), [])
        self.assertEqual(len(_run(rq.check_oversized, files)), 1)

    def test_uses_actual_readme_name_in_path(self):
        files = {"Readme.md": "a" * (README_SIZE_LIMIT + 1)}
        findings = _run(rq.check_oversized, files)
        self.assertEqual(findings[0].path, "Readme.md")


if __name__ == "__main__":
    unittest.main()
