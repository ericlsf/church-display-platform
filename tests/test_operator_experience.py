import unittest

from services.operator_experience import _parse_time


class OperatorExperienceTests(unittest.TestCase):
    def test_parse_time_accepts_zulu(self):
        value = _parse_time("2026-07-15T12:00:00Z")
        self.assertIsNotNone(value)
        self.assertIsNotNone(value.tzinfo)


if __name__ == "__main__":
    unittest.main()
