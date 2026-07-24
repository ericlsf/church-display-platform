import unittest
from unittest.mock import patch

from services.display_upgrades import display_upgrade_state


class DisplayUpgradeTests(unittest.TestCase):
    @patch(
        "services.display_upgrades.list_display_release_tags",
        return_value=["v5.3.1", "v5.4.0"],
    )
    @patch(
        "services.display_upgrades.latest_display_tag",
        return_value="v5.4.0",
    )
    @patch(
        "services.display_upgrades.list_jobs",
        return_value=[],
    )
    def test_update_available(
        self,
        _jobs,
        _latest,
        _tags,
    ):
        state = display_upgrade_state(
            "welcome-center",
            "v5.3.1",
        )

        self.assertTrue(
            state["update_available"]
        )
        self.assertEqual(
            state["latest_version"],
            "v5.4.0",
        )


if __name__ == "__main__":
    unittest.main()
