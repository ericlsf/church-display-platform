import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


DISPLAY_DIR = Path(__file__).resolve().parents[1] / "display"
if str(DISPLAY_DIR) not in sys.path:
    sys.path.insert(0, str(DISPLAY_DIR))

from agent import hub_connection


class DualHubConnectivityTests(unittest.TestCase):
    def setUp(self):
        self.original_urls = hub_connection._hub_urls
        self.original_active = hub_connection._active_hub_url
        self.original_file = hub_connection.ENDPOINTS_FILE

    def tearDown(self):
        hub_connection._hub_urls = self.original_urls
        hub_connection._active_hub_url = self.original_active
        hub_connection.ENDPOINTS_FILE = self.original_file

    def test_fails_over_and_remembers_working_endpoint(self):
        hub_connection._hub_urls = (
            "http://church-display-hub.local:8090",
            "https://hub.example.org",
        )
        hub_connection._active_hub_url = hub_connection._hub_urls[0]
        attempts = []
        response = Mock()

        def fake_urlopen(request, timeout):
            attempts.append(request.full_url)
            if request.full_url.startswith(
                "http://church-display-hub.local"
            ):
                raise OSError("LAN unavailable")
            return response

        with patch.object(
            hub_connection.urllib.request,
            "urlopen",
            side_effect=fake_urlopen,
        ):
            self.assertIs(
                hub_connection.open_hub("/api/v1/jobs/next"),
                response,
            )
            self.assertEqual(
                attempts,
                [
                    "http://church-display-hub.local:8090"
                    "/api/v1/jobs/next",
                    "https://hub.example.org/api/v1/jobs/next",
                ],
            )
            self.assertEqual(
                hub_connection.active_hub_url(),
                "https://hub.example.org",
            )

            attempts.clear()
            hub_connection.open_hub("/api/v1/heartbeat")
            self.assertEqual(
                attempts,
                ["https://hub.example.org/api/v1/heartbeat"],
            )

    def test_discovered_hub_urls_are_persisted(self):
        with tempfile.TemporaryDirectory() as temp_name:
            endpoint_file = Path(temp_name) / "hub_endpoints.json"
            hub_connection.ENDPOINTS_FILE = endpoint_file
            hub_connection._hub_urls = ("http://old-hub.local:8090",)
            hub_connection._active_hub_url = hub_connection._hub_urls[0]

            hub_connection.update_hub_urls([
                "http://church-display-hub.local:8090/",
                "https://hub.example.org/",
                "not-a-url",
            ])

            self.assertEqual(
                hub_connection.hub_urls(),
                (
                    "http://old-hub.local:8090",
                    "http://church-display-hub.local:8090",
                    "https://hub.example.org",
                ),
            )
            saved = json.loads(
                endpoint_file.read_text(encoding="utf-8")
            )
            self.assertEqual(
                saved["urls"][:2],
                [
                    "http://church-display-hub.local:8090",
                    "https://hub.example.org",
                ],
            )

    def test_installer_supports_public_fallback_url(self):
        installer = (
            Path(__file__).resolve().parents[1]
            / "hub"
            / "static"
            / "install-display-bootstrap.sh"
        ).read_text(encoding="utf-8")

        self.assertIn("DEFAULT_PUBLIC_HUB_URL", installer)
        self.assertIn("--fallback-hub-url", installer)


if __name__ == "__main__":
    unittest.main()
