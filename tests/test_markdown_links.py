"""Tests for README local link/image checks (offline)."""

import tempfile
import unittest
from pathlib import Path

from repoready.rules.context import build_context
from repoready.rules import markdown_links as ml


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


class SkipTests(unittest.TestCase):
    def test_no_readme_skips_link_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = build_context(Path(tmp))
            for check in ml.CHECKS:
                self.assertIsNone(check(ctx), msg=check.__name__)


class SlugTests(unittest.TestCase):
    def test_github_style_slug(self):
        self.assertEqual(ml.github_slug("Getting Started!"), "getting-started")
        self.assertEqual(ml.github_slug("Install (pip)"), "install-pip")
        self.assertEqual(ml.github_slug("使用说明"), "使用说明")
        self.assertEqual(ml.github_slug("  API  Reference  "), "api--reference")

    def test_duplicate_headings_get_numbered_anchors(self):
        text = "## Dup\n\n## Dup\n\n### Dup\n"
        anchors = ml._slug_anchors(text)
        self.assertEqual(anchors, {"dup", "dup-1", "dup-2"})

    def test_trailing_hashes_stripped(self):
        text = "## Setup ##\n"
        self.assertEqual(ml._slug_anchors(text), {"setup"})


class LinkTargetTests(unittest.TestCase):
    def test_passes_for_existing_relative_target(self):
        files = {
            "README.md": "# T\n\nRead the [guide](docs/guide.md).\n",
            "docs/guide.md": "# Guide\n",
        }
        self.assertEqual(_run(ml.check_link_targets, files), [])

    def test_broken_link_is_error_with_line_evidence(self):
        files = {"README.md": "# T\n\nSee [the guide](missing.md).\n"}
        findings = _run(ml.check_link_targets, files)
        self.assertEqual(len(findings), 1)
        finding = findings[0]
        self.assertEqual(finding.rule_id, "link.target.missing")
        self.assertEqual(finding.severity, "error")
        self.assertEqual(finding.path, "README.md")
        self.assertIn("line 3", finding.evidence)
        self.assertIn("missing.md", finding.evidence)

    def test_broken_image_is_reported(self):
        files = {"README.md": "![logo](assets/logo.png)\n"}
        findings = _run(ml.check_link_targets, files)
        self.assertEqual(len(findings), 1)
        self.assertIn("assets/logo.png", findings[0].evidence)

    def test_link_escaping_root_is_broken(self):
        files = {"README.md": "[x](../outside.md)\n", "outside.md": "x\n"}
        findings = _run(ml.check_link_targets, files)
        self.assertEqual(len(findings), 1)
        self.assertIn("outside the repository root", findings[0].evidence)

    def test_url_encoded_target_resolves(self):
        files = {"README.md": "[x](my%20file.md)\n", "my file.md": "x\n"}
        self.assertEqual(_run(ml.check_link_targets, files), [])

    def test_backslash_separator_resolves(self):
        files = {"README.md": "[x](docs\\guide.md)\n", "docs/guide.md": "x\n"}
        self.assertEqual(_run(ml.check_link_targets, files), [])

    def test_directory_target_resolves(self):
        files = {"README.md": "[docs](docs/)\n", "docs/": None}
        self.assertEqual(_run(ml.check_link_targets, files), [])

    def test_root_relative_target_resolves(self):
        files = {"README.md": "[x](/docs/guide.md)\n", "docs/guide.md": "x\n"}
        self.assertEqual(_run(ml.check_link_targets, files), [])

    def test_fenced_example_links_are_ignored(self):
        files = {
            "README.md": "# T\n\n```\n[not a link](missing.md)\n```\n",
        }
        self.assertEqual(_run(ml.check_link_targets, files), [])

    def test_reference_links_resolve(self):
        files = {
            "README.md": "# T\n\nSee [guide][g] and [docs][].\n\n"
                         "[g]: docs/guide.md\n[docs]: <docs/other.md> \"Docs\"\n",
            "docs/guide.md": "x\n",
            "docs/other.md": "x\n",
        }
        self.assertEqual(_run(ml.check_link_targets, files), [])

    def test_undefined_reference_is_not_checked(self):
        files = {"README.md": "See [guide][undefined-ref].\n"}
        self.assertEqual(_run(ml.check_link_targets, files), [])

    def test_external_links_never_flagged_missing(self):
        files = {"README.md": "[site](https://example.com/a.md)\n"}
        self.assertEqual(_run(ml.check_link_targets, files), [])

    def test_empty_destination_skipped(self):
        files = {"README.md": "[x]()\n"}
        self.assertEqual(_run(ml.check_link_targets, files), [])


class AnchorTests(unittest.TestCase):
    def test_passes_for_matching_readme_anchor(self):
        files = {"README.md": "# Install\n\n[go](#install)\n"}
        self.assertEqual(_run(ml.check_anchors, files), [])

    def test_broken_readme_anchor_is_info(self):
        files = {"README.md": "# Install\n\n[go](#nope)\n"}
        findings = _run(ml.check_anchors, files)
        self.assertEqual(len(findings), 1)
        finding = findings[0]
        self.assertEqual(finding.rule_id, "link.anchor.not-found")
        self.assertEqual(finding.severity, "info")
        self.assertIn("#nope (line 3)", finding.evidence)

    def test_target_file_anchors_checked(self):
        files = {
            "README.md": "[i](docs/g.md#setup)\n",
            "docs/g.md": "## Setup\n",
        }
        self.assertEqual(_run(ml.check_anchors, files), [])

    def test_target_file_anchor_mismatch_is_info(self):
        files = {
            "README.md": "[i](docs/g.md#steup)\n",
            "docs/g.md": "## Setup\n",
        }
        findings = _run(ml.check_anchors, files)
        self.assertEqual(len(findings), 1)
        self.assertIn("docs/g.md#steup", findings[0].evidence)

    def test_duplicate_numbered_anchors_match(self):
        files = {
            "README.md": "## Dup\n\n## Dup\n\n[d1](#dup-1)\n",
        }
        self.assertEqual(_run(ml.check_anchors, files), [])

    def test_non_markdown_target_anchor_skipped(self):
        files = {
            "README.md": "[p](docs/x.pdf#page=2)\n",
            "docs/x.pdf": "%PDF fake\n",
        }
        self.assertEqual(_run(ml.check_anchors, files), [])

    def test_missing_target_anchor_skipped_here(self):
        # The broken path is reported by link.target.missing; the anchor
        # rule must not double-report it.
        files = {"README.md": "[x](missing.md#a)\n"}
        self.assertEqual(_run(ml.check_anchors, files), [])

    def test_hyphenated_anchor_matches_spaces_in_heading(self):
        files = {"README.md": "# Get Started!\n\n[go](#get-started)\n"}
        self.assertEqual(_run(ml.check_anchors, files), [])

    def test_percent20_anchor_does_not_match_hyphenated_slug(self):
        # GitHub parity: %20 does not match the hyphenated slug.
        files = {"README.md": "# Get Started!\n\n[go](#get%20started)\n"}
        findings = _run(ml.check_anchors, files)
        self.assertEqual(len(findings), 1)


class ExternalTests(unittest.TestCase):
    def test_no_external_links_passes(self):
        files = {"README.md": "[x](docs/x.md)\n", "docs/x.md": "x\n"}
        self.assertEqual(_run(ml.check_external, files), [])

    def test_single_external_link_is_counted(self):
        findings = _run(ml.check_external, {"README.md": "[site](https://example.com)\n"})
        self.assertEqual(len(findings), 1)
        finding = findings[0]
        self.assertEqual(finding.rule_id, "link.external-not-checked")
        self.assertEqual(finding.severity, "info")
        self.assertIn("1 external links", finding.evidence)

    def test_mailto_and_multiple_links_counted(self):
        files = {
            "README.md": (
                "[mail](mailto:a@b.c) [one](https://a.io) "
                "[two](http://b.io) [local](docs/x.md)\n"
            ),
            "docs/x.md": "x\n",
        }
        findings = _run(ml.check_external, files)
        self.assertEqual(len(findings), 1)
        self.assertIn("3 external links", findings[0].evidence)


if __name__ == "__main__":
    unittest.main()
