import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DisplayFleetV1100Tests(unittest.TestCase):
    def test_display_workspace_assets_and_controls(self):
        template = (ROOT / "hub/templates/displays.html").read_text()
        self.assertIn("display-fleet-v1100.css", template)
        self.assertIn("Save assignments", template)
        self.assertIn('name="sync_folder"', template)
        self.assertIn('name="group_ids"', template)
        self.assertIn('name="profile_id"', template)
        self.assertIn("Latest screenshot", template)

    def test_workspace_route_queues_and_persists_assignments(self):
        route = (ROOT / "hub/routes/displays.py").read_text()
        self.assertIn('/<display_id>/workspace', route)
        self.assertIn('"set_sync_folder"', route)
        self.assertIn("apply_profile(profile_id", route)
        self.assertIn("update_group(", route)
        self.assertIn('display["assigned_folder"] = folder', route)

    def test_fleet_actions_can_return_to_display_workspace(self):
        route = (ROOT / "hub/routes/fleet.py").read_text()
        self.assertIn("def _redirect_back", route)
        self.assertIn('request.form.get("next"', route)


if __name__ == "__main__":
    unittest.main()
