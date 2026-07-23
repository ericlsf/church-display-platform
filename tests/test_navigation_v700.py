import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

class NavigationV700CompatibilityTests(unittest.TestCase):
    def test_base_includes_current_shell_once(self):
        text = (ROOT / "hub/templates/base.html").read_text(encoding="utf-8")
        self.assertEqual(text.count('{% include "application_shell.html" %}'), 1)

    def test_current_shell_assets_exist(self):
        text = (ROOT / "hub/templates/base.html").read_text(encoding="utf-8")
        self.assertEqual(text.count("/static/application-shell.css"), 1)
        self.assertEqual(text.count("/static/application-shell.js"), 1)

    def test_old_home_link_is_not_in_current_navigation(self):
        shell = (ROOT / "hub/templates/application_shell.html").read_text(encoding="utf-8")
        self.assertNotIn(">Home<", shell)

    def test_sidebar_sections_exist(self):
        shell = (ROOT / "hub/templates/application_shell.html").read_text(encoding="utf-8")
        for section in ("Dashboard", "Fleet", "Media", "Operations", "Administration"):
            self.assertIn(section, shell)

if __name__ == "__main__":
    unittest.main()
