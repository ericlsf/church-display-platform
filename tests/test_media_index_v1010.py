#!/usr/bin/env python3
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hub"))

from services import media_index


class MediaIndexTests(unittest.TestCase):
    def test_cached_analysis_does_not_call_rclone(self):
        fixture = {
            "remote": "gdrive", "status": "ready", "updated_at": "2026-07-18T12:00:00+00:00", "error": "",
            "items": [
                {"Path": "Sunday/Welcome.jpg", "Name": "Welcome.jpg", "IsDir": False, "Size": 1024, "ModTime": "2026-07-18T10:00:00Z", "MimeType": "image/jpeg"},
                {"Path": "Sunday/Clips", "Name": "Clips", "IsDir": True, "Size": 0, "ModTime": "", "MimeType": "inode/directory"},
                {"Path": "Sunday/Clips/Intro.mp4", "Name": "Intro.mp4", "IsDir": False, "Size": 2048, "ModTime": "2026-07-18T10:00:00Z", "MimeType": "video/mp4"},
            ],
        }
        with patch.object(media_index, "load_media_index", return_value=fixture), patch.object(media_index, "get_playlist_order", return_value=[]):
            with patch("subprocess.run", side_effect=AssertionError("request path must not call rclone")):
                result = media_index.analyze_cached_folder("gdrive", "Sunday")
        self.assertEqual(result["images"], 1)
        self.assertEqual(result["folders"], 1)
        self.assertEqual(result["videos"], 0)

    def test_recursive_cached_analysis_includes_descendants(self):
        fixture = {
            "remote": "gdrive", "status": "ready", "updated_at": "now", "error": "",
            "items": [
                {"Path": "Sunday/Welcome.jpg", "IsDir": False, "Size": 1},
                {"Path": "Sunday/Clips/Intro.mp4", "IsDir": False, "Size": 2},
            ],
        }
        with patch.object(media_index, "load_media_index", return_value=fixture), patch.object(media_index, "get_playlist_order", return_value=[]):
            result = media_index.analyze_cached_folder("gdrive", "Sunday", recursive=True)
        self.assertEqual(result["images"], 1)
        self.assertEqual(result["videos"], 1)

    def test_media_route_uses_cache_service(self):
        source = (ROOT / "hub/routes/media.py").read_text()
        page_body = source.split("def media_page():", 1)[1].split("@media_bp.route(\"/refresh\"", 1)[0]
        self.assertIn("cached_drive_folders", page_body)
        self.assertIn("analyze_cached_folder", page_body)
        self.assertNotIn("list_drive_folders", page_body)
        self.assertNotIn("analyze_drive_folder", page_body)
        self.assertNotIn("subprocess.run", page_body)


if __name__ == "__main__":
    unittest.main()
