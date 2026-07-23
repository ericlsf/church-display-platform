import unittest

from services.display_groups import normalize_members


class DisplayGroupTests(unittest.TestCase):
    def test_members_are_deduplicated(self):
        self.assertEqual(
            normalize_members(
                ["welcome-center", "welcome-center", "", "lobby"]
            ),
            ["welcome-center", "lobby"],
        )


if __name__ == "__main__":
    unittest.main()
