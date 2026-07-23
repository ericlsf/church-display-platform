import unittest

from services.display_releases import _include


class DisplayReleasePathTests(unittest.TestCase):
    def test_runtime_directories_are_excluded(self):
        self.assertFalse(_include("display/media/example.png"))
        self.assertFalse(_include("display/venv/bin/python"))
        self.assertFalse(_include("display/config/config.json"))

    def test_runtime_source_is_included(self):
        self.assertTrue(_include("display/app/main.py"))
        self.assertTrue(_include("display/agent/agent.py"))
        self.assertTrue(_include("display/scripts/sync_media.sh"))
        self.assertTrue(_include("display/requirements.txt"))


if __name__ == "__main__":
    unittest.main()
