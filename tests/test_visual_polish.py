import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class VisualPolishTests(unittest.TestCase):
    def test_assets_exist(self):
        for path in (
            ROOT / "hub/static/operator-polish.css",
            ROOT / "hub/static/live-display-health.js",
        ):
            self.assertTrue(path.is_file(), str(path))

    def test_css_has_responsive_breakpoint(self):
        text = (
            ROOT / "hub/static/operator-polish.css"
        ).read_text(encoding="utf-8")
        self.assertIn("@media", text)


if __name__ == "__main__":
    unittest.main()
