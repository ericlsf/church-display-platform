import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class NavigationV700Tests(unittest.TestCase):
    def test_sidebar_sections_exist(self):
        text = (
            ROOT
            / "hub/templates/navigation_shell.html"
        ).read_text(encoding="utf-8")

        for section in (
            "Dashboard",
            "Fleet",
            "Media",
            "Operations",
            "Administration",
        ):
            self.assertIn(section, text)

    def test_old_home_link_is_not_in_new_navigation(self):
        text = (
            ROOT
            / "hub/templates/navigation_shell.html"
        ).read_text(encoding="utf-8")

        self.assertNotIn(
            '>Home<',
            text,
        )

    def test_navigation_assets_exist(self):
        script = (
            ROOT
            / "hub/static/navigation-v7.js"
        )
        css = (
            ROOT
            / "hub/static/style.css"
        ).read_text(encoding="utf-8")

        self.assertTrue(script.is_file())
        self.assertIn(
            "v7.0.0 navigation redesign",
            css,
        )
        self.assertIn(
            ".v7-sidebar",
            css,
        )

    def test_base_includes_shell_once(self):
        text = (
            ROOT
            / "hub/templates/base.html"
        ).read_text(encoding="utf-8")

        self.assertEqual(
            text.count(
                '{% include "navigation_shell.html" %}'
            ),
            1,
        )


if __name__ == "__main__":
    unittest.main()
