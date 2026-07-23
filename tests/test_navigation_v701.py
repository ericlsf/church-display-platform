import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class NavigationV701Tests(unittest.TestCase):
    def test_vertical_sidebar_css_exists(self):
        css = (
            ROOT
            / "hub/static/style.css"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "v7.0.1 sidebar vertical layout fix",
            css,
        )
        self.assertIn(
            "flex-direction: column !important",
            css,
        )
        self.assertIn(
            "overflow-x: hidden !important",
            css,
        )

    def test_layout_enforcement_script_exists(self):
        script = (
            ROOT
            / "hub/static/navigation-v7.1.js"
        )

        self.assertTrue(script.is_file())

        text = script.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "enforceVerticalLayout",
            text,
        )
        self.assertIn(
            "MutationObserver",
            text,
        )


if __name__ == "__main__":
    unittest.main()
