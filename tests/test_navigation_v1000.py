import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELL = (ROOT / "hub/templates/application_shell.html").read_text()
BASE = (ROOT / "hub/templates/base.html").read_text()
JS = (ROOT / "hub/static/application-shell.js").read_text()


class NavigationV1000Tests(unittest.TestCase):
    def test_six_primary_sections_exist(self):
        for label in ["Dashboard", "Command Center", "Media Library", "Displays", "Schedules", "Settings"]:
            self.assertIn(f'"{label}"', SHELL)

    def test_command_center_is_visible(self):
        self.assertIn('(\"/command-center\", \"⚡\", \"Operator Cockpit\")', SHELL)
        self.assertIn('href="/command-center">Open Command Center</a>', BASE)

    def test_command_center_routes_are_grouped(self):
        for route in ["/command-center", "/alerts", "/jobs", "/fleet-operations", "/history"]:
            self.assertIn(route, JS)
        self.assertIn('["/command-center","command"', JS)

    def test_schedule_routes_are_grouped(self):
        for route in ["/schedules", "/rollouts", "/deployments", "/bulk-operations"]:
            self.assertIn(route, JS)


if __name__ == "__main__":
    unittest.main()
