"""Tests for TOML config loading and context-level ignore filtering."""

import tempfile
import unittest
from pathlib import Path

from reporead.config import Config, ConfigError, load_config
from reporead.rules.context import build_context


def _load(text: str) -> Config:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "reporead.toml"
        path.write_text(text, encoding="utf-8")
        return load_config(path)


class LoadConfigTests(unittest.TestCase):
    def test_empty_config_yields_defaults(self):
        config = _load("")
        self.assertEqual(config.disabled_rules, frozenset())
        self.assertEqual(config.ignore_paths, ())

    def test_valid_config_loads_both_tables(self):
        config = _load(
            '[rules]\ndisable = ["repo.coc.missing"]\n\n'
            '[ignore]\npaths = ["drafts/", "notes/*.md"]\n'
        )
        self.assertEqual(config.disabled_rules, frozenset({"repo.coc.missing"}))
        self.assertEqual(config.ignore_paths, ("drafts/", "notes/*.md"))

    def test_unknown_top_level_key_rejected(self):
        with self.assertRaises(ConfigError) as ctx:
            _load('[thresholds]\nmin = 80\n')
        self.assertIn("thresholds", str(ctx.exception))

    def test_unknown_key_in_rules_table_rejected(self):
        with self.assertRaises(ConfigError) as ctx:
            _load('[rules]\nenable = ["repo.coc.missing"]\n')
        self.assertIn("enable", str(ctx.exception))

    def test_unknown_key_in_ignore_table_rejected(self):
        with self.assertRaises(ConfigError) as ctx:
            _load('[ignore]\nglobs = ["x"]\n')
        self.assertIn("globs", str(ctx.exception))

    def test_disable_with_unregistered_rule_id_rejected(self):
        with self.assertRaises(ConfigError) as ctx:
            _load('[rules]\ndisable = ["not.a.rule"]\n')
        self.assertIn("not.a.rule", str(ctx.exception))

    def test_disable_with_non_string_entry_rejected(self):
        with self.assertRaises(ConfigError) as ctx:
            _load("[rules]\ndisable = [1]\n")
        self.assertIn("array of rule_id strings", str(ctx.exception))

    def test_rules_must_be_table(self):
        with self.assertRaises(ConfigError) as ctx:
            _load("rules = 5\n")
        self.assertIn("'rules' must be a table", str(ctx.exception))

    def test_absolute_ignore_path_rejected(self):
        with self.assertRaises(ConfigError) as ctx:
            _load('[ignore]\npaths = ["/etc"]\n')
        self.assertIn("absolute", str(ctx.exception))

    def test_windows_drive_path_rejected(self):
        with self.assertRaises(ConfigError) as ctx:
            _load('[ignore]\npaths = ["C:/temp"]\n')
        self.assertIn("absolute", str(ctx.exception))

    def test_parent_escape_rejected(self):
        with self.assertRaises(ConfigError) as ctx:
            _load('[ignore]\npaths = ["../outside"]\n')
        self.assertIn("..", str(ctx.exception))

    def test_nested_escape_rejected(self):
        with self.assertRaises(ConfigError) as ctx:
            _load('[ignore]\npaths = ["docs/../../x"]\n')
        self.assertIn("..", str(ctx.exception))

    def test_missing_file_raises_config_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "no-such.toml"
            with self.assertRaises(ConfigError) as ctx:
                load_config(missing)
        self.assertIn("cannot read config", str(ctx.exception))

    def test_invalid_toml_raises_config_error(self):
        with self.assertRaises(ConfigError) as ctx:
            _load("[rules\ndisable = \n")
        self.assertIn("not valid TOML", str(ctx.exception))


class ContextIgnoreTests(unittest.TestCase):
    def _repo(self, root: Path):
        (root / "README.md").write_text("# T\n", encoding="utf-8")
        (root / "drafts").mkdir()
        (root / "drafts" / "wip.md").write_text("x\n", encoding="utf-8")
        (root / "docs").mkdir()
        (root / "docs" / "guide.md").write_text("x\n", encoding="utf-8")

    def test_ignored_root_entry_becomes_invisible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._repo(root)
            ctx = build_context(root, ignore_paths=("README.md",))
            names = {e.name for e in ctx.root_entries}
            self.assertNotIn("README.md", names)
            self.assertIn("drafts", names)

    def test_dir_prefix_hides_whole_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._repo(root)
            ctx = build_context(root, ignore_paths=("drafts/",))
            names = {e.name for e in ctx.root_entries}
            self.assertNotIn("drafts", names)

    def test_glob_hides_docs_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._repo(root)
            ctx = build_context(root, ignore_paths=("docs/*.md",))
            self.assertEqual(ctx.docs_files_lower, frozenset())

    def test_without_ignore_everything_visible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._repo(root)
            ctx = build_context(root)
            self.assertEqual(
                {e.name for e in ctx.root_entries}, {"README.md", "drafts", "docs"}
            )


if __name__ == "__main__":
    unittest.main()
