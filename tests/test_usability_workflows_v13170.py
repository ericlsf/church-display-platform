import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import services.display_profiles as profiles
import services.media as media


class UsabilityWorkflowTests(unittest.TestCase):
    def test_starter_presets_are_installed_once(self):
        with tempfile.TemporaryDirectory() as temp:
            profile_file = Path(temp) / "display_profiles.json"
            with patch.object(profiles, "PROFILES_FILE", profile_file):
                created = profiles.install_starter_profiles(actor="admin")
                repeated = profiles.install_starter_profiles(actor="admin")

                self.assertEqual(len(created), 6)
                self.assertEqual(repeated, [])
                stored = profiles.load_profiles()["profiles"]
                self.assertEqual(len(stored), 6)
                emergency = next(
                    profile for profile in stored
                    if profile["name"] == "Emergency Message"
                )
                self.assertFalse(emergency["settings"]["clock"]["enabled"])
                self.assertFalse(emergency["settings"]["countdown"]["enabled"])

    def test_expired_media_is_automatically_excluded(self):
        with tempfile.TemporaryDirectory() as temp:
            playlist_file = Path(temp) / "playlists.json"
            playlist_file.write_text(json.dumps({
                "playlists": {
                    "gdrive:Weekly": {
                        "published_excluded": ["manual.jpg"],
                        "expirations": {
                            "past.jpg": "2000-01-01",
                            "future.jpg": "2999-01-01",
                        },
                    },
                },
            }))
            with patch.object(media, "PLAYLISTS_FILE", playlist_file):
                excluded = media.get_playlist_exclusions("gdrive", "Weekly")

            self.assertEqual(excluded, ["manual.jpg", "past.jpg"])

    def test_version_matches_usability_release(self):
        version = Path("hub/VERSION").read_text(encoding="utf-8").strip()
        self.assertEqual(version, "v13.20.0")


if __name__ == "__main__":
    unittest.main()
