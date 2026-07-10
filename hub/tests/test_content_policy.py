import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services import content_cache


class ContentPolicyTests(unittest.TestCase):
    def setUp(self):
        self.current = {
            "old.jpg": {"modified": "2026-01-01T00:00:00Z", "size": 1},
            "new.jpg": {"modified": "2026-07-01T00:00:00Z", "size": 1},
        }
        self.data = {"playlists": {"gdrive:Weekly": {
            "order": ["old.jpg"],
            "files": {"old.jpg": self.current["old.jpg"]},
        }}}

    @patch.object(content_cache, "save_playlists")
    @patch.object(content_cache, "load_playlists")
    @patch.object(content_cache, "get_playlist_policy", return_value="newest_first")
    def test_newest_first(self, policy, load, save):
        load.return_value = self.data
        order, changed, chosen = content_cache._reconcile_order("gdrive", "Weekly", self.current)
        self.assertEqual(order[0], "new.jpg")
        self.assertEqual(chosen, "newest_first")

    @patch.object(content_cache, "save_playlists")
    @patch.object(content_cache, "load_playlists")
    @patch.object(content_cache, "get_playlist_policy", return_value="newest_last")
    def test_newest_last(self, policy, load, save):
        load.return_value = self.data
        order, changed, chosen = content_cache._reconcile_order("gdrive", "Weekly", self.current)
        self.assertEqual(order[-1], "new.jpg")


if __name__ == "__main__":
    unittest.main()
