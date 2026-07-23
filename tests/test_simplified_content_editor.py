import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class SimplifiedContentEditorTests(unittest.TestCase):
    def test_preview_removed(self):
        template = (
            ROOT
            / "hub/templates/display_details.html"
        ).read_text(encoding="utf-8")

        self.assertNotIn(
            "content-preview-card",
            template,
        )
        self.assertNotIn(
            "content-overlay-editor.js",
            template,
        )

    def test_checkbox_size_is_constrained(self):
        css = (
            ROOT
            / "hub/static/style.css"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "v5.9.3 simplified content editor",
            css,
        )
        self.assertIn(
            'input[type="checkbox"]',
            css,
        )
        self.assertIn(
            "width: 1.05rem !important",
            css,
        )


if __name__ == "__main__":
    unittest.main()
