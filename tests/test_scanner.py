"""Unit tests for the read-only scanner boundary."""

import os
import tempfile
import unittest
from pathlib import Path

import fixture_builders as fb
from reporead.scanner import ScannerError, iter_files, resolve_root


class ResolveRootTests(unittest.TestCase):
    def test_nonexistent_path_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "no-such-dir"
            with self.assertRaises(ScannerError):
                resolve_root(missing)

    def test_file_path_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "file.txt"
            target.write_text("x", encoding="utf-8")
            with self.assertRaises(ScannerError):
                resolve_root(target)

    def test_valid_dir_resolves_to_absolute(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = resolve_root(tmp)
            self.assertTrue(root.is_absolute())
            self.assertEqual(root, Path(tmp).resolve())


class IterFilesTests(unittest.TestCase):
    def test_lists_files_sorted_and_skips_frozen_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            (root / ".git" / "config").write_text("", encoding="utf-8")
            (root / "node_modules").mkdir()
            (root / "node_modules" / "x.js").write_text("", encoding="utf-8")
            (root / "build").mkdir()
            (root / "build" / "z").write_text("", encoding="utf-8")
            (root / "sub").mkdir()
            (root / "a.txt").write_text("", encoding="utf-8")
            (root / "sub" / "b.txt").write_text("", encoding="utf-8")

            names = [str(p.relative_to(root)) for p in iter_files(root)]
            self.assertEqual(names, ["a.txt", os.path.join("sub", "b.txt")])

            again = [str(p.relative_to(root)) for p in iter_files(root)]
            self.assertEqual(names, again)

    def test_does_not_follow_directory_symlinks_out_of_root(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp) / "repo"
            link = fb.make_repo_with_symlink_escape(root, Path(outside))
            if link is None:
                self.skipTest("symlink creation not permitted on this platform")
            names = [p.name for p in iter_files(root)]
            self.assertNotIn("secret.txt", names)

    def test_enumerates_without_executing_target_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fb.make_repo_with_never_execute_payload(Path(tmp))
            names = [p.name for p in iter_files(root)]
            self.assertIn("evil.py", names)
            self.assertFalse((root / "EXECUTED_MARKER").exists())

    def test_enumeration_does_not_open_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fb.make_repo_with_unreadable_file(Path(tmp))
            try:
                names = [p.name for p in iter_files(root)]
            finally:
                # Restore access before tempdir cleanup (Windows: clears
                # the read-only attribute so the file can be deleted).
                os.chmod(root / "locked.txt", 0o644)
            self.assertIn("locked.txt", names)

    def test_oversized_markdown_is_listed_not_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fb.make_repo_with_oversized_markdown(Path(tmp))
            names = [p.name for p in iter_files(root)]
            self.assertIn("README.md", names)
            self.assertEqual(
                (root / "README.md").stat().st_size, fb.OVERSIZED_MARKDOWN_BYTES
            )

    def test_windows_style_paths_are_listed_intact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fb.make_repo_with_windows_style_paths(Path(tmp))
            relative = [str(p.relative_to(root)) for p in iter_files(root)]
            self.assertEqual(
                relative,
                [os.path.join("docs with spaces", "中文 (v2)", "note.md")],
            )


if __name__ == "__main__":
    unittest.main()
