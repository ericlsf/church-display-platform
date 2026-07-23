import unittest
from unittest.mock import patch
import agent.version as version

class VersionApiCompatibilityTests(unittest.TestCase):
    @patch("agent.version.installed_version", return_value="5.6.3")
    @patch("agent.version.git_metadata", return_value={
        "branch": "main",
        "commit": "abc123",
        "tag": "v5.6.3",
        "describe": "v5.6.3",
        "dirty": "no",
    })
    def test_legacy_version_info_shape(self, _git, _installed):
        result = version.get_version_info()
        self.assertEqual(result["version"], "5.6.3")
        self.assertEqual(result["tag"], "5.6.3")
        self.assertEqual(result["commit"], "abc123")
        self.assertIn("git", result)

if __name__ == "__main__":
    unittest.main()
