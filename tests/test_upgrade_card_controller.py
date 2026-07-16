import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class UpgradeCardControllerTests(unittest.TestCase):
    def test_controller_keeps_manage_action(self):
        path = (
            ROOT
            / "hub/static/live-deployment-status.js"
        )
        text = path.read_text(encoding="utf-8")

        self.assertIn(
            "Manage Versions",
            text,
        )
        self.assertIn(
            "Version verified",
            text,
        )
        self.assertNotIn(
            "if (form) form.hidden = true",
            text,
        )


if __name__ == "__main__":
    unittest.main()
