import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class OperatorUiV800Tests(unittest.TestCase):
    def test_navigation_has_sidebar_search(self):
        text = (
            ROOT
            / "hub/templates/navigation_shell.html"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "v8-sidebar-search",
            text,
        )

    def test_navigation_uses_grouped_workspaces(self):
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

    def test_compact_dimensions_exist(self):
        css = (
            ROOT
            / "hub/static/style.css"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "--v8-sidebar-width: 232px",
            css,
        )
        self.assertIn(
            "--v8-topbar-height: 58px",
            css,
        )

    def test_current_group_behavior_exists(self):
        script = (
            ROOT
            / "hub/static/navigation-v8.js"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "openGroup",
            script,
        )
        self.assertIn(
            "route.section",
            script,
        )


if __name__ == "__main__":
    unittest.main()
