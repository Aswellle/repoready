"""Tests for release metadata consistency rules (pyproject/package.json/changelog)."""

import json
import tempfile
import unittest
from pathlib import Path

from repoready.rules.context import build_context
from repoready.rules import release_metadata as rm


def _run(check, files: dict[str, str | None]):
    """Build a temp repo from {relative_name: content}; None = directory."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for name, content in files.items():
            target = root / name
            if content is None:
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
        findings = check(build_context(root))
    return findings


def json_dumps(data) -> str:
    return json.dumps(data, indent=2) + "\n"


FULL_PYPROJECT = (
    "[project]\n"
    'name = "demo"\n'
    'version = "0.1.0"\n'
    'description = "Demo project."\n'
    'readme = "README.md"\n'
    'license = "MIT"\n'
)


class PyprojectTests(unittest.TestCase):
    def test_skips_without_pyproject(self):
        self.assertIsNone(_run(rm.check_pyproject_fields, {}))

    def test_passes_with_all_required_fields(self):
        files = {"pyproject.toml": FULL_PYPROJECT}
        self.assertEqual(_run(rm.check_pyproject_fields, files), [])

    def test_missing_field_reports_once_per_field(self):
        minimal = '[project]\nname = "demo"\n'
        findings = _run(rm.check_pyproject_fields, {"pyproject.toml": minimal})
        rule_ids = [f.rule_id for f in findings]
        self.assertEqual(set(rule_ids), {"meta.pyproject.required-fields"})
        self.assertEqual(len(findings), 4)  # version, description, readme, license
        for finding in findings:
            self.assertEqual(finding.severity, "warning")
            self.assertEqual(finding.path, "pyproject.toml")
        titles = " | ".join(f.title for f in findings)
        self.assertIn("'version'", titles)
        self.assertIn("'description'", titles)
        self.assertIn("'readme'", titles)
        self.assertIn("'license'", titles)
        self.assertNotIn("'name'", titles)

    def test_dynamic_listed_field_counts_as_present(self):
        files = {
            "pyproject.toml": (
                "[project]\n"
                'name = "demo"\n'
                'description = "d"\n'
                'readme = "README.md"\n'
                'license = "MIT"\n'
                'dynamic = ["version"]\n'
            )
        }
        self.assertEqual(_run(rm.check_pyproject_fields, files), [])

    def test_license_files_alternative_accepted(self):
        files = {
            "pyproject.toml": (
                "[project]\n"
                'name = "demo"\n'
                'version = "0.1.0"\n'
                'description = "d"\n'
                'readme = "README.md"\n'
                'license-files = ["LICENSE"]\n'
            )
        }
        self.assertEqual(_run(rm.check_pyproject_fields, files), [])

    def test_missing_project_table_reports_once(self):
        files = {"pyproject.toml": '[tool.black]\nline-length = 88\n'}
        findings = _run(rm.check_pyproject_fields, files)
        self.assertEqual(len(findings), 1)
        self.assertIn("[project]", findings[0].title)

    def test_invalid_toml_reports_format_finding(self):
        files = {"pyproject.toml": "[project\nname = broken\n"}
        findings = _run(rm.check_pyproject_fields, files)
        self.assertEqual(len(findings), 1)
        self.assertIn("not valid TOML", findings[0].title)
        self.assertIn("TOML parse error", findings[0].evidence)


class PackageJsonTests(unittest.TestCase):
    def test_skips_without_package_json(self):
        self.assertIsNone(_run(rm.check_packagejson_fields, {}))

    def test_passes_with_all_required_fields(self):
        files = {
            "package.json": json_dumps(
                {"name": "demo", "version": "0.1.0",
                 "description": "d", "license": "MIT"}
            )
        }
        self.assertEqual(_run(rm.check_packagejson_fields, files), [])

    def test_missing_fields_reported_individually(self):
        files = {"package.json": json_dumps({"name": "demo"})}
        findings = _run(rm.check_packagejson_fields, files)
        self.assertEqual(len(findings), 3)
        titles = " | ".join(f.title for f in findings)
        for field in ("version", "description", "license"):
            self.assertIn(f"'{field}'", titles)

    def test_invalid_json_reports_format_finding(self):
        files = {"package.json": "{not json"}
        findings = _run(rm.check_packagejson_fields, files)
        self.assertEqual(len(findings), 1)
        self.assertIn("not valid JSON", findings[0].title)

    def test_non_object_root_reported(self):
        files = {"package.json": "[1, 2]\n"}
        findings = _run(rm.check_packagejson_fields, files)
        self.assertEqual(len(findings), 1)
        self.assertIn("not a JSON object", findings[0].title)


class ChangelogTests(unittest.TestCase):
    def test_skips_without_changelog(self):
        self.assertIsNone(_run(rm.check_changelog_entry, {}))

    def test_passes_with_version_heading(self):
        files = {"CHANGELOG.md": "# Changelog\n\n## 0.1.0\n\n- initial\n"}
        self.assertEqual(_run(rm.check_changelog_entry, files), [])

    def test_passes_with_setext_version_heading(self):
        # ripgrep-style plain-text changelog: version line + === underline.
        files = {
            "CHANGELOG.md": "TBD\n===\n\n15.2.0 (2026-07-15)\n===========\n\nfixes\n"
        }
        self.assertEqual(_run(rm.check_changelog_entry, files), [])

    def test_passes_with_unreleased_heading(self):
        files = {"CHANGELOG.md": "## Unreleased\n\n- wip\n"}
        self.assertEqual(_run(rm.check_changelog_entry, files), [])

    def test_passes_keep_a_changelog_bracket_style(self):
        files = {"CHANGELOG.md": "## [1.2.3] - 2026-01-01\n\n- fixed\n"}
        self.assertEqual(_run(rm.check_changelog_entry, files), [])

    def test_passes_v_prefixed_version(self):
        files = {"CHANGELOG.md": "## v0.2.0\n\n- added\n"}
        self.assertEqual(_run(rm.check_changelog_entry, files), [])

    def test_fails_without_version_heading(self):
        files = {"CHANGELOG.md": "# Changelog\n\nSome prose only.\n"}
        findings = _run(rm.check_changelog_entry, files)
        self.assertEqual(len(findings), 1)
        finding = findings[0]
        self.assertEqual(finding.rule_id, "meta.changelog.current-entry")
        self.assertEqual(finding.severity, "info")
        self.assertEqual(finding.path, "CHANGELOG.md")

    def test_single_number_heading_does_not_count(self):
        files = {"CHANGELOG.md": "## 2\n\nprose\n"}
        self.assertEqual(len(_run(rm.check_changelog_entry, files)), 1)

    def test_version_heading_inside_fence_does_not_count(self):
        files = {"CHANGELOG.md": "```\n## 1.0.0\n```\nprose\n"}
        self.assertEqual(len(_run(rm.check_changelog_entry, files)), 1)

    def test_docs_releases_md_alternative(self):
        files = {"docs/releases.md": "# Releases\n\n## 0.3.0\n"}
        self.assertEqual(_run(rm.check_changelog_entry, files), [])
        files = {"docs/releases.md": "# Releases\n\nprose only\n"}
        findings = _run(rm.check_changelog_entry, files)
        self.assertEqual(findings[0].path, "docs/releases.md")


if __name__ == "__main__":
    unittest.main()
