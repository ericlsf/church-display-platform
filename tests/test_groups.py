import unittest
from unittest.mock import patch

from services.groups import normalize_display_ids


class GroupTests(unittest.TestCase):
    @patch("services.groups.valid_display_ids", return_value={"a", "b"})
    def test_normalize_members(self, _):
        self.assertEqual(normalize_display_ids(["a", "a", "x", "b"]), ["a", "b"])


if __name__ == "__main__":
    unittest.main()
