import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import services.display_profiles as profiles


class DisplayProfileTests(unittest.TestCase):
    def test_settings_are_normalized(self):
        result = profiles.normalize_settings({
            "overlay": {
                "enabled": "false",
                "text": "  Hello  ",
            },
            "countdown": {
                "start_minutes": 999,
            },
            "timings": {
                "image_duration": 0,
            },
        })

        self.assertFalse(result["overlay"]["enabled"])
        self.assertEqual(
            result["overlay"]["text"],
            "Hello",
        )
        self.assertEqual(
            result["countdown"]["start_minutes"],
            180,
        )
        self.assertEqual(
            result["timings"]["image_duration"],
            1,
        )

    def test_profile_history_is_created_on_update(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "profiles.json"

            with patch.object(
                profiles,
                "PROFILES_FILE",
                path,
            ):
                created = profiles.save_profile(
                    "",
                    "Lobby",
                    "",
                    profiles.DEFAULT_SETTINGS,
                    actor="admin",
                )

                updated = profiles.save_profile(
                    created["id"],
                    "Lobby Updated",
                    "",
                    profiles.DEFAULT_SETTINGS,
                    actor="admin",
                )

                self.assertEqual(
                    updated["name"],
                    "Lobby Updated",
                )
                self.assertEqual(
                    len(updated["history"]),
                    1,
                )
                self.assertEqual(
                    updated["history"][0]["name"],
                    "Lobby",
                )

    def test_export_import_round_trip(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "profiles.json"

            with patch.object(
                profiles,
                "PROFILES_FILE",
                path,
            ):
                created = profiles.save_profile(
                    "",
                    "Sanctuary",
                    "No overlay",
                    {
                        "overlay": {
                            "enabled": False,
                            "text": "",
                        },
                    },
                    actor="admin",
                )

                payload = profiles.export_profile(
                    created["id"]
                )
                imported = profiles.import_profile(
                    payload,
                    actor="admin",
                )

                self.assertEqual(
                    imported["name"],
                    "Sanctuary",
                )
                self.assertFalse(
                    imported["settings"]["overlay"][
                        "enabled"
                    ]
                )


if __name__ == "__main__":
    unittest.main()
