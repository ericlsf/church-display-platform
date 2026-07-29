import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


DISPLAY_DIR = Path(__file__).resolve().parents[1] / "display"
if str(DISPLAY_DIR) not in sys.path:
    sys.path.insert(0, str(DISPLAY_DIR))

from agent import hub_connection
from agent.jobs.update import _download


class DisplayUpdateDownloadTests(unittest.TestCase):
    def setUp(self):
        self.original_urls = hub_connection._hub_urls
        self.original_active = hub_connection._active_hub_url
        hub_connection._hub_urls = (
            "https://hub.example.org",
            "http://church-display-hub.local:8090",
        )
        hub_connection._active_hub_url = hub_connection._hub_urls[0]

    def tearDown(self):
        hub_connection._hub_urls = self.original_urls
        hub_connection._active_hub_url = self.original_active

    @staticmethod
    def response(body, content_type, checksum=""):
        response = Mock()
        response.headers = {
            "Content-Type": content_type,
            "Content-Length": str(len(body)),
        }
        if checksum:
            response.headers["X-Checksum-SHA256"] = checksum
        response.read = io.BytesIO(body).read
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        return response

    def test_cloudflare_login_page_falls_back_to_lan_package(self):
        package = b"\x1f\x8bdisplay-release"
        login = self.response(b"<html>Sign in</html>", "text/html")
        release = self.response(package, "application/octet-stream")
        attempts = []

        def fake_urlopen(request, timeout):
            attempts.append(request.full_url)
            return login if len(attempts) == 1 else release

        with tempfile.TemporaryDirectory() as temp_name:
            destination = Path(temp_name) / "release.tar.gz"
            with patch.object(
                hub_connection.urllib.request,
                "urlopen",
                side_effect=fake_urlopen,
            ):
                _download(
                    "https://hub.example.org/api/v1/display-releases/"
                    "artifacts/abc.tar.gz",
                    destination,
                    lambda *_args: None,
                )

            self.assertEqual(destination.read_bytes(), package)
            self.assertEqual(len(attempts), 2)
            self.assertTrue(
                attempts[1].startswith(
                    "http://church-display-hub.local:8090/"
                )
            )
            self.assertEqual(
                hub_connection.active_hub_url(),
                "http://church-display-hub.local:8090",
            )

    def test_html_response_is_rejected_for_direct_download(self):
        response = self.response(b"<html>Sign in</html>", "text/html")
        with tempfile.TemporaryDirectory() as temp_name:
            destination = Path(temp_name) / "release.tar.gz"
            with patch(
                "agent.jobs.update.request.urlopen",
                return_value=response,
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "did not return a software package",
                ):
                    _download(
                        "https://downloads.example.org/release.tar.gz",
                        destination,
                        lambda *_args: None,
                    )


if __name__ == "__main__":
    unittest.main()
