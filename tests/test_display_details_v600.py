import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class DisplayDetailsV600Tests(unittest.TestCase):
    def test_operator_header_and_summary_exist(self):
        text = (
            ROOT / "hub/templates/display_details.html"
        ).read_text(encoding="utf-8")

        self.assertIn('class="display-hero"', text)
        self.assertIn('class="display-summary-grid"', text)
        self.assertIn('class="health-list-v600"', text)

    def test_compact_css_exists(self):
        css = (
            ROOT / "hub/static/style.css"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "v6.0.0 display details UX refresh",
            css,
        )
        self.assertIn(
            "grid-template-columns: repeat(4, minmax(0, 1fr))",
            css,
        )


if __name__ == "__main__":
    unittest.main()
