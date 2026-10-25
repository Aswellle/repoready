"""Tests for shared markdown text utilities."""

import tempfile
import unittest
from pathlib import Path

from reporead.rules.markdown_text import (
    README_SIZE_LIMIT,
    has_fenced_code,
    iter_unfenced_lines,
    read_capped,
)


class UnfencedLineTests(unittest.TestCase):
    def test_plain_lines_pass_through_with_line_numbers(self):
        text = "first\nsecond\n"
        self.assertEqual(
            list(iter_unfenced_lines(text)), [(1, "first"), (2, "second")]
        )

    def test_backtick_fence_content_is_skipped(self):
        text = (
            "# Title\n"
            "```bash\n"
            "# not a heading\n"
            "[x](missing.md)\n"
            "```\n"
            "after\n"
        )
        lines = list(iter_unfenced_lines(text))
        self.assertEqual(
            [(n, l) for n, l in lines],
            [(1, "# Title"), (6, "after")],
        )

    def test_tilde_fence_with_info_string(self):
        text = "a\n~~~python\nignored\n~~~\nb\n"
        self.assertEqual(
            list(iter_unfenced_lines(text)),
            [(1, "a"), (5, "b")],
        )

    def test_closing_fence_requires_bare_marker(self):
        # "```python" inside an open ``` block is literal text in
        # CommonMark and must not close the fence.
        text = "```\ncode\n```python\nstill code\n```\nafter\n"
        lines = list(iter_unfenced_lines(text))
        self.assertEqual(lines, [(6, "after")])

    def test_longer_close_run_closes_shorter_open(self):
        text = "```\nx\n``````\nafter\n"
        self.assertEqual(list(iter_unfenced_lines(text)), [(4, "after")])

    def test_indented_fence_opens(self):
        text = "a\n   ```\nhidden\n   ```\nb\n"
        self.assertEqual(
            list(iter_unfenced_lines(text)), [(1, "a"), (5, "b")]
        )

    def test_unclosed_fence_skips_rest_of_file(self):
        text = "a\n```\nnever closed\n"
        self.assertEqual(list(iter_unfenced_lines(text)), [(1, "a")])

    def test_four_space_indent_does_not_open_fence(self):
        # 4-space indent is an indented code block, not a fence opener;
        # the bare ``` on line 3 opens (and never closes) a real fence.
        text = "    ```\nnot a fence\n```\n"
        lines = list(iter_unfenced_lines(text))
        self.assertEqual(lines, [(1, "    ```"), (2, "not a fence")])


class HasFencedCodeTests(unittest.TestCase):
    def test_detects_fenced_block(self):
        self.assertTrue(has_fenced_code("a\n```\nx\n```\n"))

    def test_tilde_block_detected(self):
        self.assertTrue(has_fenced_code("a\n~~~\nx\n~~~\n"))

    def test_unclosed_block_counts_as_fenced(self):
        self.assertTrue(has_fenced_code("a\n```\nx\n"))

    def test_plain_text_has_no_fence(self):
        self.assertFalse(has_fenced_code("# head\n\nbody `code` span\n"))


class ReadCappedTests(unittest.TestCase):
    def test_small_file_read_whole(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "README.md"
            path.write_text("# hello\n", encoding="utf-8")
            text, truncated = read_capped(path)
            self.assertEqual(text, "# hello\n")
            self.assertFalse(truncated)

    def test_oversized_file_truncated_at_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "README.md"
            payload = "a" * (README_SIZE_LIMIT + 1024)
            path.write_text(payload, encoding="utf-8")
            text, truncated = read_capped(path)
            self.assertTrue(truncated)
            self.assertEqual(len(text), README_SIZE_LIMIT)

    def test_invalid_utf8_degrades_with_replacement(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "README.md"
            path.write_bytes(b"# \xff\xfe bad bytes\n")
            text, truncated = read_capped(path)
            self.assertFalse(truncated)
            self.assertIn("# ", text)


if __name__ == "__main__":
    unittest.main()
