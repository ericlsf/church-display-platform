import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class DisplaySettingsLayoutTests(unittest.TestCase):
    def test_layout_classes_exist(self):
        template = (
            ROOT
            / "hub/templates/display_details.html"
        ).read_text(encoding="utf-8")

        self.assertIn(
            'class="display-settings-layout"',
            template,
        )
        self.assertIn(
            'class="display-settings-content-row"',
            template,
        )
        self.assertIn(
            'class="display-settings-secondary-row"',
            template,
        )

    def test_full_width_content_css_exists(self):
        css = (
            ROOT
            / "hub/static/style.css"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "v5.9.2 display settings layout",
            css,
        )
        self.assertIn(
            "grid-column: 1 / -1",
            css,
        )
        self.assertIn(
            "repeat(2, minmax(0, 1fr))",
            css,
        )


if __name__ == "__main__":
    unittest.main()
