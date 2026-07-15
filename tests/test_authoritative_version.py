import tempfile
import unittest
from pathlib import Path

from agent.install_version import record_installed_release


class AuthoritativeVersionTests(unittest.TestCase):
    def test_release_is_recorded_atomically(self):
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)

            record_installed_release(
                root,
                "v5.6.0",
                sha256="abc123",
            )

            self.assertEqual(
                (root / "VERSION").read_text().strip(),
                "v5.6.0",
            )

            self.assertIn(
                '"version": "v5.6.0"',
                (root / "release.json").read_text(),
            )


if __name__ == "__main__":
    unittest.main()
