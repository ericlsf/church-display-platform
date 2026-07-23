import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import services.resilience as resilience


class ResilienceTests(unittest.TestCase):
    def test_defaults_and_maintenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "resilience.json"
            with patch.object(resilience, "SETTINGS_FILE", path):
                data = resilience.load_resilience()
                self.assertTrue(data["recovery"]["enabled"])
                self.assertEqual(data["backups"]["interval_days"], 14)
                resilience.set_maintenance(True, "Testing")
                updated = resilience.load_resilience()
                self.assertTrue(updated["maintenance"]["enabled"])
                self.assertEqual(updated["maintenance"]["message"], "Testing")


if __name__ == "__main__":
    unittest.main()
