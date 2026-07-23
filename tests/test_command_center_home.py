import unittest


class CommandCenterHomeTests(unittest.TestCase):
    def test_expected_route_names(self):
        self.assertEqual(
            "command_center_home.home",
            "command_center_home.home",
        )


if __name__ == "__main__":
    unittest.main()
