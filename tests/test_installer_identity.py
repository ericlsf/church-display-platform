import unittest


def normalize(value):
    import re
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


class InstallerIdentityTests(unittest.TestCase):
    def test_hostname_to_stable_id(self):
        self.assertEqual(normalize("Welcome-Center"), "welcome-center")

    def test_spaces_and_dots_preserve_boundaries(self):
        self.assertEqual(normalize("Main Lobby.TV"), "main-lobby-tv")


if __name__ == "__main__":
    unittest.main()
