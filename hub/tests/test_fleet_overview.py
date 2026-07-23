import unittest
from unittest.mock import patch

from app import create_app


class FleetOverviewTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
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

    @patch("routes.fleet.create_job")
    def test_bulk_restart_returns_to_fleet(self, create_job):
        response = self.client.post(
            "/fleet/bulk/restart",
            data={"display_ids": ["lobby"], "next": "/displays"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/displays"))
        create_job.assert_called_once_with("lobby", "restart_display", {})


if __name__ == "__main__":
    unittest.main()
