"""Registry, rule-context and per-rule tests for the checks engine."""

import re
import tempfile
import unittest
from pathlib import Path

from reporead.models import SEVERITIES
from reporead.rules.context import build_context
from reporead.rules import run_checks
from reporead.rules import community_files as cf
from reporead.rules import repository_files as rf
from reporead.rules.registry import REGISTRY, get_spec

DOCS_TABLE = (
    Path(__file__).resolve().parents[1]
    / "docs" / "spec" / "01-architecture-rules.md"
)

RULE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(\.[a-z0-9_-]+)+$")


def _doc_rules() -> dict[str, str]:
    """Parse the §2a rule table from the architecture doc."""
    rows: dict[str, str] = {}
    for line in DOCS_TABLE.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\|\s*`([^`]+)`\s*\|\s*(error|warning|info)\s*\|", line)
        if match:
            rows[match.group(1)] = match.group(2)
    return rows


class RegistryTests(unittest.TestCase):
    def test_rule_ids_are_unique(self):
        ids = [spec.rule_id for spec in REGISTRY]
        self.assertEqual(len(ids), len(set(ids)))

    def test_rule_ids_follow_naming_convention(self):
        for spec in REGISTRY:
            self.assertRegex(
                spec.rule_id, RULE_ID_PATTERN, msg=f"bad rule_id: {spec.rule_id}"
            )

    def test_severities_and_categories_are_known_values(self):
        categories = {"essential", "community", "readme", "links", "metadata"}
        for spec in REGISTRY:
            self.assertIn(spec.severity, SEVERITIES, msg=spec.rule_id)
            self.assertIn(spec.category, categories, msg=spec.rule_id)

    def test_registry_matches_documented_rule_table(self):
        doc = _doc_rules()
        code = {spec.rule_id: spec.severity for spec in REGISTRY}
        self.assertEqual(code, doc)

    def test_get_spec_rejects_unknown_rule_id(self):
        with self.assertRaises(LookupError):
            get_spec("not.a.rule")


# (rule_id, builder that creates ONLY this element in a fresh temp root)
ESSENTIAL_CASES = (
    ("repo.readme.missing",
     lambda root: (root / "README.md").write_text("# demo\n", encoding="utf-8")),
    ("repo.license.missing",
     lambda root: (root / "LICENSE").write_text("MIT License\n", encoding="utf-8")),
    ("repo.manifest.missing",
     lambda root: (root / "pyproject.toml").write_text(
         "[project]\nname = 'demo'\n", encoding="utf-8")),
    ("repo.gitignore.missing",
     lambda root: (root / ".gitignore").write_text(
         "__pycache__/\n", encoding="utf-8")),
    ("repo.tests.missing",
     lambda root: (root / "tests").mkdir()),
    ("repo.ci.missing",
     lambda root: (
         (root / ".github" / "workflows").mkdir(parents=True),
         (root / ".github" / "workflows" / "ci.yml").write_text(
             "on: push\n", encoding="utf-8"),
     )),
)

ESSENTIAL_CHECKS = {
    "repo.readme.missing": rf.check_readme,
    "repo.license.missing": rf.check_license,
    "repo.manifest.missing": rf.check_manifest,
    "repo.gitignore.missing": rf.check_gitignore,
    "repo.tests.missing": rf.check_tests,
    "repo.ci.missing": rf.check_ci,
}


class EssentialRuleTests(unittest.TestCase):
    def _run_case(self, rule_id, builder):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            builder(root)
            return ESSENTIAL_CHECKS[rule_id](build_context(root)), root

    def test_each_essential_rule_passes_when_element_present(self):
        for rule_id, builder in ESSENTIAL_CASES:
            with self.subTest(rule_id=rule_id):
                findings, _ = self._run_case(rule_id, builder)
                self.assertEqual(findings, [])

    def test_each_essential_rule_fails_on_empty_repo(self):
        for rule_id, _ in ESSENTIAL_CASES:
            with self.subTest(rule_id=rule_id):
                with tempfile.TemporaryDirectory() as tmp:
                    findings = ESSENTIAL_CHECKS[rule_id](build_context(Path(tmp)))
                self.assertEqual(len(findings), 1)
                finding = findings[0]
                self.assertEqual(finding.rule_id, rule_id)
                self.assertEqual(finding.severity, get_spec(rule_id).severity)
                self.assertTrue(finding.title)
                self.assertTrue(finding.detail)
                self.assertTrue(finding.suggestion)

    def test_findings_carry_evidence_and_expected_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            findings = rf.check_readme(build_context(Path(tmp)))
        self.assertIsNotNone(findings[0].path)
        self.assertIsNotNone(findings[0].evidence)
        with tempfile.TemporaryDirectory() as tmp:
            manifest = rf.check_manifest(build_context(Path(tmp)))
            tests = rf.check_tests(build_context(Path(tmp)))
        self.assertIsNone(manifest[0].path)
        self.assertIsNone(tests[0].path)


class EssentialRuleEdgeTests(unittest.TestCase):
    def _one(self, rule_id, root):
        return ESSENTIAL_CHECKS[rule_id](build_context(root))

    def test_readme_matches_case_insensitive_variants(self):
        for name in ("Readme.md", "readme.MD", "README"):
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    (root / name).write_text("# x\n", encoding="utf-8")
                    self.assertEqual(self._one("repo.readme.missing", root), [])

    def test_license_matches_case_insensitive_variants(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "LICENSE.TXT").write_text("x\n", encoding="utf-8")
            self.assertEqual(self._one("repo.license.missing", root), [])

    def test_gitignore_requires_exact_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".Gitignore").write_text("x\n", encoding="utf-8")
            findings = self._one("repo.gitignore.missing", root)
        self.assertEqual(len(findings), 1)

    def test_manifest_matches_case_insensitive_variants(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Cargo.TOML").write_text("[package]\n", encoding="utf-8")
            self.assertEqual(self._one("repo.manifest.missing", root), [])

    def test_tests_rule_accepts_dir_case_variant_and_config_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Test").mkdir()
            self.assertEqual(self._one("repo.tests.missing", root), [])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
            self.assertEqual(self._one("repo.tests.missing", root), [])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test_app.py").write_text("", encoding="utf-8")
            self.assertEqual(self._one("repo.tests.missing", root), [])

    def test_ci_rule_accepts_github_yaml_and_root_ci_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workflows = root / ".github" / "workflows"
            workflows.mkdir(parents=True)
            (workflows / "build.yaml").write_text("on: push\n", encoding="utf-8")
            self.assertEqual(self._one("repo.ci.missing", root), [])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".gitlab-ci.yml").write_text("test:\n", encoding="utf-8")
            self.assertEqual(self._one("repo.ci.missing", root), [])

    def test_ci_rule_ignores_non_workflow_files_in_workflows_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workflows = root / ".github" / "workflows"
            workflows.mkdir(parents=True)
            (workflows / "README.txt").write_text("notes\n", encoding="utf-8")
            findings = self._one("repo.ci.missing", root)
        self.assertEqual(len(findings), 1)


# (rule_id, builder that creates ONLY this element in a fresh temp root)
COMMUNITY_CASES = (
    ("repo.contributing.missing",
     lambda root: (root / "CONTRIBUTING.md").write_text(
         "# contributing\n", encoding="utf-8")),
    ("repo.security.missing",
     lambda root: (root / "SECURITY.md").write_text(
         "# security\n", encoding="utf-8")),
    ("repo.coc.missing",
     lambda root: (root / "CODE_OF_CONDUCT.md").write_text(
         "# conduct\n", encoding="utf-8")),
    ("repo.changelog.missing",
     lambda root: (root / "CHANGELOG.md").write_text(
         "# changelog\n", encoding="utf-8")),
    ("repo.templates.issues.missing",
     lambda root: (
         (root / ".github" / "ISSUE_TEMPLATE").mkdir(parents=True),
         (root / ".github" / "ISSUE_TEMPLATE" / "bug_report.md").write_text(
             "steps\n", encoding="utf-8"),
     )),
    ("repo.templates.pr.missing",
     lambda root: (
         (root / ".github").mkdir(),
         (root / ".github" / "PULL_REQUEST_TEMPLATE.md").write_text(
             "summary\n", encoding="utf-8"),
     )),
)

COMMUNITY_CHECKS = {
    "repo.contributing.missing": cf.check_contributing,
    "repo.security.missing": cf.check_security,
    "repo.coc.missing": cf.check_coc,
    "repo.changelog.missing": cf.check_changelog,
    "repo.templates.issues.missing": cf.check_issue_templates,
    "repo.templates.pr.missing": cf.check_pr_template,
}


class CommunityRuleTests(unittest.TestCase):
    def _run_case(self, rule_id, builder):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            builder(root)
            return COMMUNITY_CHECKS[rule_id](build_context(root)), root

    def test_each_community_rule_passes_when_element_present(self):
        for rule_id, builder in COMMUNITY_CASES:
            with self.subTest(rule_id=rule_id):
                findings, _ = self._run_case(rule_id, builder)
                self.assertEqual(findings, [])

    def test_each_community_rule_fails_on_empty_repo(self):
        for rule_id, _ in COMMUNITY_CASES:
            with self.subTest(rule_id=rule_id):
                with tempfile.TemporaryDirectory() as tmp:
                    findings = COMMUNITY_CHECKS[rule_id](build_context(Path(tmp)))
                self.assertEqual(len(findings), 1)
                finding = findings[0]
                self.assertEqual(finding.rule_id, rule_id)
                self.assertEqual(finding.severity, get_spec(rule_id).severity)
                self.assertTrue(finding.title)
                self.assertTrue(finding.detail)
                self.assertTrue(finding.suggestion)


class CommunityRuleEdgeTests(unittest.TestCase):
    def _one(self, rule_id, root):
        return COMMUNITY_CHECKS[rule_id](build_context(root))

    def test_community_files_match_case_insensitive_variants(self):
        for rule_id, name in (
            ("repo.contributing.missing", "contributing.MD"),
            ("repo.security.missing", "Security.md"),
            ("repo.coc.missing", "code_of_conduct.MD"),
        ):
            with self.subTest(rule_id=rule_id, name=name):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    (root / name).write_text("x\n", encoding="utf-8")
                    self.assertEqual(self._one(rule_id, root), [])

    def test_changelog_accepts_docs_releases_md_alternative(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            releases = root / "docs"
            releases.mkdir()
            (releases / "releases.md").write_text("# 0.1.0\n", encoding="utf-8")
            self.assertEqual(self._one("repo.changelog.missing", root), [])

    def test_issue_template_dir_must_contain_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".github" / "ISSUE_TEMPLATE").mkdir(parents=True)
            findings = self._one("repo.templates.issues.missing", root)
        self.assertEqual(len(findings), 1)

    def test_pr_template_accepts_dir_form_under_github(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".github" / "PULL_REQUEST_TEMPLATE").mkdir(parents=True)
            (root / ".github" / "PULL_REQUEST_TEMPLATE" / "default.md").write_text(
                "summary\n", encoding="utf-8"
            )
            self.assertEqual(self._one("repo.templates.pr.missing", root), [])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pull_request_template.md").write_text(
                "summary\n", encoding="utf-8"
            )
            self.assertEqual(self._one("repo.templates.pr.missing", root), [])


class EngineTests(unittest.TestCase):
    FIXTURES = Path(__file__).resolve().parent / "fixtures"

    def test_complete_golden_repo_passes(self):
        findings, evaluated = run_checks(self.FIXTURES / "golden_complete_repo")
        self.assertEqual(findings, ())
        self.assertEqual(evaluated, 21)

    def test_empty_root_skips_readme_dependent_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            findings, evaluated = run_checks(Path(tmp))
        # 12 always-applicable rules; the 7 README-dependent rules skip.
        self.assertEqual(evaluated, 12)
        self.assertEqual(len(findings), 12)
        for finding in findings:
            self.assertEqual(finding.severity, get_spec(finding.rule_id).severity)

    def test_readme_only_repo_evaluates_content_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# T\n", encoding="utf-8")
            findings, evaluated = run_checks(root)
        self.assertEqual(evaluated, 19)
        rule_ids = [f.rule_id for f in findings]
        self.assertNotIn("repo.readme.missing", rule_ids)
        self.assertIn("readme.install-not-detected", rule_ids)
        self.assertIn("readme.usage-not-detected", rule_ids)

    def test_run_order_is_stable_across_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = run_checks(Path(tmp))
            second = run_checks(Path(tmp))
        self.assertEqual(first, second)

    def test_all_emitted_rule_ids_are_registered(self):
        registered = {spec.rule_id for spec in REGISTRY}
        with tempfile.TemporaryDirectory() as tmp:
            findings, _ = run_checks(Path(tmp))
        self.assertTrue({f.rule_id for f in findings} <= registered)


if __name__ == "__main__":
    unittest.main()
