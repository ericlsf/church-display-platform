import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent.jobs.settings import _clean_settings


class DisplaySettingsTests(unittest.TestCase):
    def test_settings_are_bounded_and_cleaned(self):
        result = _clean_settings({
            "overlay": {"enabled": False, "text": "  Hello  "},
            "clock": {"enabled": False},
            "countdown": {"enabled": True, "start_minutes": 999},
            "timings": {"image_duration": 0},
        })

        self.assertFalse(result["overlay"]["enabled"])
        self.assertEqual(result["overlay"]["text"], "Hello")
        self.assertEqual(result["countdown"]["start_minutes"], 180)
        self.assertEqual(result["timings"]["image_duration"], 1)


if __name__ == "__main__":
    unittest.main()
