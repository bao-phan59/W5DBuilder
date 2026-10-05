"""Behavior checks for bounded reads and resumable section cursors."""
import tempfile
import unittest
from pathlib import Path

from doc_slice import read_slice


class DocSliceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.doc = self.root / "doc.md"

    def write(self, value):
        self.doc.write_text(value, encoding="utf-8-sig")

    def test_section_and_vietnamese_bom(self):
        self.write("# Tài liệu\n## WP0\nKiểm thử voi\n### Gate\nĐúng\n## WP1\nKhông đọc\n")
        result = read_slice(self.root, "doc.md", section="## WP0")
        self.assertIn("Kiểm thử voi", result)
        self.assertIn("### Gate", result)
        self.assertNotIn("Không đọc", result)
        self.assertIn("next_line=6", result)

    def test_fenced_heading_is_not_section_boundary(self):
        self.write("## WP0\n```md\n## WP1\n```\ntext\n## WP2\nend\n")
        result = read_slice(self.root, "doc.md", section="## WP0")
        self.assertIn("5: text", result)
        self.assertNotIn("7: end", result)
        index = read_slice(self.root, "doc.md", heading_only=True)
        self.assertNotIn("3: ## WP1", index)

    def test_bound_and_resume(self):
        self.write("## WP0\n" + "payload " * 8 + "\n" + "value\n" * 40 + "## WP1\n")
        first = read_slice(self.root, "doc.md", section="## WP0", max_chars=400)
        self.assertLessEqual(len(first), 400)
        self.assertIn("TRUNCATED", first)
        cursor = int(first.split("next_line=")[1].split(";")[0])
        resumed = read_slice(self.root, "doc.md", section="## WP0", start=cursor)
        self.assertIn(f"{cursor}: ", resumed)
        self.assertIn("COMPLETE_SLICE", resumed)

    def test_long_line_makes_no_false_progress(self):
        self.write("X" * 2000)
        result = read_slice(self.root, "doc.md", max_chars=400)
        self.assertLessEqual(len(result), 400)
        self.assertIn("TRUNCATED next_line=1", result)

    def test_ambiguous_section_and_invalid_cursor(self):
        self.write("## WP0 a\nx\n## WP0 b\ny\n")
        with self.assertRaises(ValueError):
            read_slice(self.root, "doc.md", section="## WP0")
        with self.assertRaises(ValueError):
            read_slice(self.root, "doc.md", section="## WP0 a", start=4)

    def test_reject_escape_and_invalid_limits(self):
        with self.assertRaises(ValueError):
            read_slice(self.root, "../outside.md")
        with self.assertRaises(ValueError):
            read_slice(self.root, "doc.md", max_chars=50)
        with self.assertRaises(ValueError):
            read_slice(self.root, "config.env")


if __name__ == "__main__":
    unittest.main()
