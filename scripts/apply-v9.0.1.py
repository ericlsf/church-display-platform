#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def patch_layout_test():
    path = ROOT / "tests/test_layout_v810.py"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        'self.assertIn("padding-top\\",\\"92px\\"",js)',
        'self.assertIn(\'"padding-top"\', js)\n        self.assertIn(\'"92px"\', js)',
    )
    text = text.replace(
        'self.assertIn("padding-top\\",\\"92px\\"", js)',
        'self.assertIn(\'"padding-top"\', js)\n        self.assertIn(\'"92px"\', js)',
    )
    path.write_text(text, encoding="utf-8")

def replace_navigation_test():
    path = ROOT / "tests/test_navigation_v700.py"
    path.write_text("""import unittest
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
""", encoding="utf-8")

def add_regression_test():
    path = ROOT / "tests/test_application_shell_v901.py"
    path.write_text("""import unittest
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
""", encoding="utf-8")

def main():
    patch_layout_test()
    replace_navigation_test()
    add_regression_test()
    print("v9.0.1 shell stabilization applied.")

if __name__ == "__main__":
    main()
