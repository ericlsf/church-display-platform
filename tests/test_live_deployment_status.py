import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class LiveDeploymentStatusTests(unittest.TestCase):
    def test_live_status_asset_exists(self):
        path = (
            ROOT
            / "hub/static/live-deployment-status.js"
        )

        self.assertTrue(path.is_file())

        text = path.read_text(encoding="utf-8")

        self.assertIn(
            "setInterval(refresh, 5000)",
            text,
        )
        self.assertIn(
            "deployment-verification",
            text,
        )
        self.assertIn(
            "deployment-timeline",
            text,
        )


if __name__ == "__main__":
    unittest.main()
