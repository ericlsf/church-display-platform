import unittest

from services.telemetry_normalization import (
    normalize_fleet_telemetry,
    normalize_media_count,
    normalize_version,
)


class TelemetryNormalizationTests(unittest.TestCase):
    def test_current_file_proves_local_media_exists(self):
        self.assertEqual(
            normalize_media_count({
                "current_file": "/opt/church-display/media/slide.jpg",
            }),
            1,
        )

    def test_nested_media_count_is_used(self):
        self.assertEqual(
            normalize_media_count({
                "media": {"local_count": 12},
            }),
            12,
        )

    def test_live_agent_version_beats_saved_version(self):
        self.assertEqual(
            normalize_version(
                {"agent": {"version": "v5.5.1"}},
                "v5.0.0",
            ),
            "v5.5.1",
        )

    def test_playback_evidence_marks_player_running(self):
        result = normalize_fleet_telemetry(
            {
                "playback": {
                    "current_file": "slide.jpg",
                    "media_count": 8,
                },
                "agent_version": "v5.5.1",
                "last_sync_status": "completed",
            },
            {"version": "v5.0.0"},
        )

        self.assertTrue(result["player_running"])
        self.assertEqual(result["media_count"], 8)
        self.assertEqual(result["version"], "v5.5.1")
        self.assertTrue(result["sync_ok"])


if __name__ == "__main__":
    unittest.main()
