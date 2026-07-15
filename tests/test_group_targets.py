import unittest
from unittest.mock import patch

from services.fleet_operations import resolve_targets


class GroupTargetTests(unittest.TestCase):
    @patch(
        "services.fleet_operations.group_members",
        return_value=["welcome-center", "lobby"],
    )
    def test_direct_and_group_targets_are_deduplicated(self, _groups):
        self.assertEqual(
            resolve_targets(
                ["welcome-center"],
                ["front-of-house"],
            ),
            ["welcome-center", "lobby"],
        )


if __name__ == "__main__":
    unittest.main()
