import unittest
from unittest.mock import patch

from app import create_app
from services.fleet_state import media_count_for, system_health_for


class FleetOverviewTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.before_request_funcs[None] = [
            handler
            for handler in self.app.before_request_funcs.get(None, [])
            if handler.__name__ != "church_display_auth_guard"
        ]
        self.client = self.app.test_client()

    @patch("routes.displays.load_config")
    @patch("routes.displays.build_fleet_state")
    def test_displays_renders_fleet_cards_and_controls(self, build_state, load_config):
        load_config.return_value = {
            "displays": [{
                "id": "lobby",
                "name": "Lobby",
                "host": "http://lobby.local",
                "username": "",
                "password": "",
            }]
        }
        build_state.return_value = {
            "rows": [{
                "id": "lobby",
                "name": "Lobby",
                "host": "http://lobby.local",
                "group": "Main",
                "online": True,
                "preview_url": "/static/previews/lobby.jpg",
                "system": {"cpu_temp": "48 C", "memory": "42%", "disk": "27%"},
                "media_count": 12,
                "current_tag": "v13.4.0",
                "version": "13.4.0",
                "heartbeat": "5 seconds ago",
                "update_available": False,
            }]
        }

        response = self.client.get("/displays")
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Fleet Overview", body)
        self.assertIn("fleet-card", body)
        self.assertIn("Search displays", body)
        self.assertIn("Select all visible", body)
        self.assertIn("12", body)
        self.assertIn("Screenshot", body)
        self.assertIn("View logs", body)
        self.assertIn("Live activity", body)
        self.assertIn("Notifications", body)

    @patch("routes.fleet.load_config")
    @patch("routes.fleet.create_job")
    def test_bulk_restart_returns_to_fleet(self, create_job, load_config):
        load_config.return_value = {"displays": [{"id": "lobby"}]}
        response = self.client.post(
            "/fleet/bulk/restart",
            data={"display_ids": ["lobby"], "next": "/displays"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/displays"))
        create_job.assert_called_once_with("lobby", "restart_display", {})

    def test_live_status_fills_media_memory_and_disk(self):
        status = {
            "total_media": 18,
            "memory": "37%",
            "disk": "22%",
            "uptime": "2 days",
        }
        heartbeat = {
            "media": {"total": 0},
            "system": {"cpu_temp": "51.2 C", "memory": "Unknown", "disk": "Unknown"},
        }

        self.assertEqual(media_count_for(status, heartbeat), 18)
        self.assertEqual(system_health_for(status, heartbeat), {
            "cpu_temp": "51.2 C",
            "memory": "37%",
            "disk": "22%",
            "uptime": "2 days",
        })

    def test_legacy_flat_heartbeat_health_is_supported(self):
        heartbeat = {
            "media_count": "9",
            "cpu_temp": "49.0 C",
            "memory_usage": "41%",
            "disk_usage": "28%",
            "uptime": "6 hours",
        }

        self.assertEqual(media_count_for({}, heartbeat), 9)
        self.assertEqual(system_health_for({}, heartbeat), {
            "cpu_temp": "49.0 C",
            "memory": "41%",
            "disk": "28%",
            "uptime": "6 hours",
        })

    @patch("routes.fleet.create_job")
    def test_screenshot_action_queues_preview_upload(self, create_job):
        response = self.client.post(
            "/fleet/lobby/screenshot",
            data={"next": "/displays"},
        )

        self.assertEqual(response.status_code, 302)
        create_job.assert_called_once_with("lobby", "upload_preview", {})

    @patch("routes.fleet.load_config")
    @patch("routes.fleet.create_job")
    def test_bulk_reboot_only_queues_configured_displays(self, create_job, load_config):
        load_config.return_value = {"displays": [{"id": "lobby"}]}
        response = self.client.post(
            "/fleet/bulk/reboot",
            data={"display_ids": ["lobby", "not-configured"], "next": "/displays"},
        )

        self.assertEqual(response.status_code, 302)
        create_job.assert_called_once_with("lobby", "reboot", {})


if __name__ == "__main__":
    unittest.main()
