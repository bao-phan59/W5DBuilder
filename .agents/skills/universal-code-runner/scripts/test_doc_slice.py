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
        self.write("# Tài liệu dự án\n## Phase 0\nCấu hình môi trường\n### Gate\nKiểm tra pass\n## Phase 1\nChưa đọc\n")
        result = read_slice(self.root, "doc.md", section="## Phase 0")
        self.assertIn("Cấu hình môi trường", result)
        self.assertIn("### Gate", result)
        self.assertNotIn("Chưa đọc", result)
        self.assertIn("next_line=6", result)

    def test_fenced_heading_is_not_section_boundary(self):
        self.write("## Phase 0\n```md\n## Phase 1\n```\ntext nội dung\n## Phase 2\nend\n")
        result = read_slice(self.root, "doc.md", section="## Phase 0")
        self.assertIn("5: text nội dung", result)
        self.assertNotIn("7: end", result)
        index = read_slice(self.root, "doc.md", heading_only=True)
        self.assertNotIn("3: ## Phase 1", index)

    def test_bound_and_resume(self):
        self.write("## Phase 0\n" + "payload " * 8 + "\n" + "value\n" * 40 + "## Phase 1\n")
        first = read_slice(self.root, "doc.md", section="## Phase 0", max_chars=400)
        self.assertLessEqual(len(first), 400)
        self.assertIn("TRUNCATED", first)
        cursor = int(first.split("next_line=")[1].split(";")[0])
        resumed = read_slice(self.root, "doc.md", section="## Phase 0", start=cursor)
        self.assertIn(f"{cursor}: ", resumed)
        self.assertIn("COMPLETE_SLICE", resumed)

    def test_long_line_makes_no_false_progress(self):
        self.write("X" * 2000)
        result = read_slice(self.root, "doc.md", max_chars=400)
        self.assertLessEqual(len(result), 400)
        self.assertIn("TRUNCATED next_line=1", result)

    def test_ambiguous_section_and_invalid_cursor(self):
        self.write("## Phase 0 a\nx\n## Phase 0 b\ny\n")
        with self.assertRaises(ValueError):
            read_slice(self.root, "doc.md", section="## Phase 0")
        with self.assertRaises(ValueError):
            read_slice(self.root, "doc.md", section="## Phase 0 a", start=4)

    def test_reject_escape_and_invalid_limits(self):
        with self.assertRaises(ValueError):
            read_slice(self.root, "../outside.md")
        with self.assertRaises(ValueError):
            read_slice(self.root, "doc.md", max_chars=50)
        with self.assertRaises(ValueError):
            read_slice(self.root, "config.env")


if __name__ == "__main__":
    unittest.main()
