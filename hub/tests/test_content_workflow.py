import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services import media


class ContentWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "playlists.json"
        self.patcher = patch.object(media, "PLAYLISTS_FILE", self.path)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.temp.cleanup()

    def test_draft_does_not_replace_published_order(self):
        media.save_playlist_order("gdrive", "Weekly", ["a.jpg", "b.jpg"])
        media.publish_playlist("gdrive", "Weekly")
        media.save_playlist_draft("gdrive", "Weekly", ["b.jpg", "a.jpg"], "reordered")
        entry = media.get_playlist_entry("gdrive", "Weekly")
        self.assertEqual(entry["published_order"], ["a.jpg", "b.jpg"])
        self.assertEqual(entry["draft_order"], ["b.jpg", "a.jpg"])
        self.assertEqual(entry["status"], "draft")

    def test_publish_promotes_draft(self):
        media.save_playlist_draft("gdrive", "Weekly", ["b.jpg", "a.jpg"])
        media.publish_playlist("gdrive", "Weekly")
        entry = media.get_playlist_entry("gdrive", "Weekly")
        self.assertEqual(entry["published_order"], ["b.jpg", "a.jpg"])
        self.assertEqual(entry["status"], "published")


if __name__ == "__main__":
    unittest.main()
