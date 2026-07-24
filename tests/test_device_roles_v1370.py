import unittest

from services.device_roles import device_role_for
from services.fleet_state import build_alerts


class DeviceRoleTests(unittest.TestCase):
    def test_explicit_roles_take_precedence(self):
        self.assertEqual(
            device_role_for(
                {"id": "church-display-hub", "device_role": "display"},
                "church-display-hub",
            ),
            "display",
        )

    def test_local_hub_is_detected_without_agent_change(self):
        self.assertEqual(
            device_role_for({"id": "church-display-hub"}, "church-display-hub"),
            "controller",
        )
        self.assertEqual(
            device_role_for({"id": "welcome-center"}, "church-display-hub"),
            "display",
        )

    def test_controller_keeps_infrastructure_alerts_only(self):
        row = {
            "id": "church-display-hub",
            "name": "Church Display Hub",
            "device_role": "controller",
            "online": True,
            "heartbeat_fresh": True,
            "sync_state": "error",
            "display_app_running": False,
            "git": {"dirty": "yes"},
            "system": {"cpu_temp": "80 C"},
        }

        alerts = build_alerts([row])
        messages = " ".join(item["message"] for item in alerts)

        self.assertNotIn("sync is reporting", messages)
        self.assertNotIn("display app is not running", messages)
        self.assertIn("uncommitted local changes", messages)

    def test_display_still_reports_player_and_sync_failures(self):
        row = {
            "id": "welcome-center",
            "name": "Welcome Center",
            "device_role": "display",
            "online": True,
            "heartbeat_fresh": True,
            "sync_state": "error",
            "display_app_running": False,
            "git": {},
            "system": {},
        }

        messages = " ".join(
            item["message"] for item in build_alerts([row])
        )
        self.assertIn("sync is reporting", messages)
        self.assertIn("display app is not running", messages)


if __name__ == "__main__":
    unittest.main()
