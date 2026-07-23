import unittest
from unittest.mock import patch
from services.command_center import command_center_data

class CommandCenterTests(unittest.TestCase):
    @patch("services.command_center.visible_notifications", return_value=[])
    @patch("services.command_center.latest_git_tag", return_value="v5.3.0")
    @patch("services.command_center._pending_displays", return_value=[])
    @patch("services.command_center.list_jobs", return_value=[])
    @patch("services.command_center.fleet_rows", return_value=[
        {"id": "welcome-center", "name": "Welcome Center", "readiness": "ready", "version": "v5.3.0"}
    ])
    def test_summary_counts_healthy_display(self, *_):
        data = command_center_data()
        self.assertEqual(data["summary"]["total"], 1)
        self.assertEqual(data["summary"]["healthy"], 1)
        self.assertEqual(data["summary"]["attention"], 0)
        self.assertEqual(data["summary"]["outdated"], 0)

    @patch("services.command_center.visible_notifications", return_value=[])
    @patch("services.command_center.latest_git_tag", return_value="v13.4.2")
    @patch("services.command_center._pending_displays", return_value=[])
    @patch("services.command_center.list_jobs", return_value=[])
    @patch("services.command_center.fleet_rows", return_value=[
        {
            "id": "welcome-center",
            "name": "Welcome Center",
            "readiness": "ready",
            "version": "v13.4.0",
            "update_available": False,
        },
        {
            "id": "lobby",
            "name": "Lobby",
            "readiness": "needs_attention",
            "version": "v13.3.1",
            "update_available": True,
        },
    ])
    def test_update_count_uses_fleet_update_compatibility(self, *_):
        data = command_center_data()
        self.assertEqual(data["summary"]["outdated"], 1)

if __name__ == "__main__":
    unittest.main()
