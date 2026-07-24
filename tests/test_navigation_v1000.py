import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELL = (ROOT / "hub/templates/application_shell.html").read_text(encoding="utf-8")
BASE = (ROOT / "hub/templates/base.html").read_text(encoding="utf-8")
JS = (ROOT / "hub/static/application-shell.js").read_text(encoding="utf-8")


class NavigationV1000Tests(unittest.TestCase):
    def test_six_task_destinations_are_primary(self):
        for route, label in [
            ("/fleet-dashboard", "Home"),
            ("/displays", "Displays"),
            ("/content", "Content"),
            ("/content-deployments", "Deployments"),
            ("/jobs", "Activity"),
            ("/alerts/", "Alerts"),
        ]:
            self.assertIn(f'("{route}",', SHELL)
            self.assertIn(f'"{label}")', SHELL)

    def test_redundant_workspaces_are_not_primary_navigation(self):
        for route in (
            "/command-center",
            "/fleet-map",
            "/fleet-operations",
            "/deployment-center",
            "/bulk-operations",
            "/history",
        ):
            self.assertNotIn(f'("{route}",', SHELL)

    def test_legacy_routes_resolve_to_task_destinations(self):
        for route in (
            "/command-center",
            "/fleet-map",
            "/fleet-operations",
            "/deployment-center",
            "/bulk-operations",
            "/history",
        ):
            self.assertIn(f'["{route}"', JS)

    def test_command_palette_uses_task_language(self):
        for label in (
            "Open Home",
            "Open Displays",
            "Open Content",
            "Deploy Content",
            "Open Activity",
            "Open Alerts",
        ):
            self.assertIn(label, BASE)
        self.assertNotIn('href="/command-center"', BASE)
        self.assertNotIn('href="/deployment-center"', BASE)


if __name__ == "__main__":
    unittest.main()
