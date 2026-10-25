"""Registry, rule-context and per-rule tests for the checks engine."""

import re
import unittest
from pathlib import Path

from reporead.models import SEVERITIES
from reporead.rules.registry import REGISTRY, RuleSpec, get_spec

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


if __name__ == "__main__":
    unittest.main()
