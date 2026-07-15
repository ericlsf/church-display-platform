import unittest

from services.deployment_guard import unique_display_ids


class RolloutTests(unittest.TestCase):
    def test_duplicate_display_ids_are_removed(self):
        self.assertEqual(
            unique_display_ids(
                ["welcome-center", "welcome-center", "lobby"]
            ),
            ["welcome-center", "lobby"],
        )


if __name__ == "__main__":
    unittest.main()
