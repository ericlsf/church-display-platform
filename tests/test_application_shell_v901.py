import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

class ApplicationShellV901Tests(unittest.TestCase):
    def test_only_current_shell_is_loaded(self):
        base = (ROOT / "hub/templates/base.html").read_text(encoding="utf-8")
        self.assertIn('{% include "application_shell.html" %}', base)
        for obsolete in (
            "navigation_shell.html",
            "navigation-v7.js",
            "navigation-v7.1.js",
            "navigation-v8.js",
            "breadcrumb-v8.1.js",
            "layout-v8.1.js",
        ):
            self.assertNotIn(obsolete, base)

    def test_shell_has_one_chrome_set(self):
        shell = (ROOT / "hub/templates/application_shell.html").read_text(encoding="utf-8")
        self.assertEqual(shell.count('class="app-sidebar"'), 1)
        self.assertEqual(shell.count('class="app-topbar"'), 1)
        self.assertEqual(shell.count('class="app-breadcrumbs"'), 1)

if __name__ == "__main__":
    unittest.main()
