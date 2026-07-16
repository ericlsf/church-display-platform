import unittest
from unittest.mock import patch
from services.fleet_truth import enrich_fleet_row

class FleetTruthTests(unittest.TestCase):
    @patch("services.fleet_truth.exact_live_telemetry", return_value={
        "media_count": 3,
        "heartbeat_version": "6.2.0",
        "version": "6.2.0",
        "player_media_count": 3,
        "media_total": 3,
        "files_synced": 3,
        "current_media": "slide.jpg",
        "received_at": "2026-07-16T12:00:00",
    })
    def test_raw_count_replaces_fallback_one(self, _telemetry):
        result = enrich_fleet_row({
            "id": "welcome-center",
            "media_count": 1,
            "version": "old",
        })
        self.assertEqual(result["media_count"], 3)
        self.assertEqual(result["version"], "6.2.0")

if __name__ == "__main__":
    unittest.main()
