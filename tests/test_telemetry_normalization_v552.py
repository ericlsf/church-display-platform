import unittest
from services.telemetry_normalization import normalize_media_count

class TelemetryNormalizationV552Tests(unittest.TestCase):
    def test_playlist_array_is_counted(self):
        self.assertEqual(
            normalize_media_count({"playlist": ["one.jpg","two.jpg","video.mp4"]}),
            3,
        )

    def test_manifest_items_are_counted(self):
        self.assertEqual(
            normalize_media_count({"manifest": {"items": [{"name":"one"},{"name":"two"}]}}),
            2,
        )

    def test_numeric_count_wins(self):
        self.assertEqual(
            normalize_media_count({"media_count": 7, "playlist": ["one.jpg"]}),
            7,
        )

if __name__ == "__main__":
    unittest.main()
