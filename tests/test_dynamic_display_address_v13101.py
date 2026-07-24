import sys
import unittest
from pathlib import Path
from unittest.mock import patch


HUB_DIR = Path(__file__).resolve().parents[1] / "hub"
if str(HUB_DIR) not in sys.path:
    sys.path.insert(0, str(HUB_DIR))

from services.display_address import refresh_approved_display_address


class DynamicDisplayAddressTests(unittest.TestCase):
    def test_updates_matching_approved_display(self):
        config = {
            "displays": [
                {
                    "id": "welcome-center",
                    "host": "http://192.168.1.110:8080",
                    "ip": "192.168.1.110",
                    "hostname": "welcome-center",
                }
            ]
        }
        heartbeat = {
            "host": "http://10.20.30.40:8080",
            "ip": "10.20.30.40",
            "hostname": "welcome-center",
        }

        with (
            patch("services.display_address.load_config", return_value=config),
            patch("services.display_address.save_config") as save_config,
        ):
            changed = refresh_approved_display_address("Welcome.Center", heartbeat)

        self.assertEqual({"host", "ip"}, changed)
        self.assertEqual("http://10.20.30.40:8080", config["displays"][0]["host"])
        self.assertEqual("10.20.30.40", config["displays"][0]["ip"])
        save_config.assert_called_once_with(config)

    def test_does_not_enroll_unknown_display(self):
        config = {"displays": [{"id": "welcome-center"}]}

        with (
            patch("services.display_address.load_config", return_value=config),
            patch("services.display_address.save_config") as save_config,
        ):
            changed = refresh_approved_display_address(
                "unknown-display",
                {"host": "http://10.20.30.50:8080", "ip": "10.20.30.50"},
            )

        self.assertEqual(set(), changed)
        save_config.assert_not_called()

    def test_unchanged_address_does_not_rewrite_config(self):
        config = {
            "displays": [
                {
                    "id": "welcome-center",
                    "host": "http://10.20.30.40:8080",
                    "ip": "10.20.30.40",
                    "hostname": "welcome-center",
                }
            ]
        }

        with (
            patch("services.display_address.load_config", return_value=config),
            patch("services.display_address.save_config") as save_config,
        ):
            changed = refresh_approved_display_address(
                "welcome-center",
                {
                    "host": "http://10.20.30.40:8080",
                    "ip": "10.20.30.40",
                    "hostname": "welcome-center",
                },
            )

        self.assertEqual(set(), changed)
        save_config.assert_not_called()


if __name__ == "__main__":
    unittest.main()
