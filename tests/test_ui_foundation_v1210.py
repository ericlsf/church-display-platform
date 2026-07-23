import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "hub" / "templates"


class UiFoundationV1210Tests(unittest.TestCase):
    def test_base_owns_shell_once(self):
        base = (TEMPLATES / "base.html").read_text(encoding="utf-8")
        self.assertEqual(base.count('{% include "application_shell.html" %}'), 1)
        self.assertIn('class="app-main"', base)
        self.assertNotIn('class="app-header"', base)
        self.assertNotIn('class="primary-nav"', base)

    def test_all_application_pages_extend_base(self):
        offenders = []
        for path in sorted(TEMPLATES.glob("*.html")):
            if path.name in {"base.html", "application_shell.html"}:
                continue
            text = path.read_text(encoding="utf-8")
            match = re.search(r'{%\s*extends\s+["\']([^"\']+)["\']\s*%}', text)
            if match and match.group(1) != "base.html":
                offenders.append(f"{path.name}: {match.group(1)}")
        self.assertEqual(offenders, [])

    def test_foundation_asset_is_global(self):
        base = (TEMPLATES / "base.html").read_text(encoding="utf-8")
        css = (ROOT / "hub" / "static" / "ui-foundation.css").read_text(encoding="utf-8")
        self.assertIn('/static/ui-foundation.css', base)
        for token in ("--ui-surface", ".ui-card", ".ui-button", ".ui-badge", ".ui-grid"):
            self.assertIn(token, css)

    def test_content_deployments_uses_shared_layout(self):
        page = (TEMPLATES / "content_deployments.html").read_text(encoding="utf-8")
        shell_js = (ROOT / "hub" / "static" / "application-shell.js").read_text(encoding="utf-8")
        self.assertTrue(page.startswith('{% extends "base.html" %}'))
        self.assertIn('["/content-deployments","schedules"', shell_js)

    def test_command_palette_includes_core_workflows(self):
        base = (TEMPLATES / "base.html").read_text(encoding="utf-8")
        for href in ("/command-center", "/media", "/displays", "/content-deployments"):
            self.assertIn(f'href="{href}"', base)


if __name__ == "__main__":
    unittest.main()
