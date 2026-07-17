import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class CommandCenterV920Tests(unittest.TestCase):
    def test_operational_hierarchy_exists(self):
        text = (ROOT / "hub/templates/command_center.html").read_text(encoding="utf-8")
        self.assertLess(text.index("Action Required"), text.index("command-metrics"))
        self.assertIn("Add Display", text)
        self.assertIn("Deploy Update", text)
        self.assertIn("Sync Media", text)
        self.assertIn("Support Bundle", text)

    def test_empty_sections_are_conditional(self):
        text = (ROOT / "hub/templates/command_center.html").read_text(encoding="utf-8")
        self.assertIn("{% if active_jobs %}", text)
        self.assertIn("{% if pending_displays %}", text)
        self.assertIn("{% if maintenance_rows %}", text)
        self.assertIn("Operations are clear", text)

    def test_live_refresh_and_toasts_exist(self):
        script = (ROOT / "hub/static/command-center.js").read_text(encoding="utf-8")
        self.assertIn("Updated just now", script)
        self.assertIn("showToast", script)
        self.assertIn("10000", script)


if __name__ == "__main__":
    unittest.main()
