import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class OverlayPreviewLayoutTests(unittest.TestCase):
    def test_preview_is_contained(self):
        css = (
            ROOT / "hub/static/style.css"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "v5.9.1 overlay preview containment",
            css,
        )
        self.assertIn(
            "grid-template-columns: minmax(0, 1fr)",
            css,
        )
        self.assertIn(
            "position: static",
            css,
        )

    def test_preview_script_limits_text(self):
        script = (
            ROOT
            / "hub/static/content-overlay-editor.js"
        ).read_text(encoding="utf-8")

        self.assertIn("fitText", script)
        self.assertIn("maxLength", script)
        self.assertIn("countdownEnabled", script)


if __name__ == "__main__":
    unittest.main()
