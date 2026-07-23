import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services.config import normalize_display_id


class EnrollmentIdentityTests(unittest.TestCase):
    def test_hostname_preserves_word_boundaries(self):
        self.assertEqual(
            normalize_display_id("Welcome-Center"),
            "welcome-center",
        )

    def test_dots_spaces_and_underscores_become_dashes(self):
        self.assertEqual(
            normalize_display_id("Welcome.Center_Test"),
            "welcome-center-test",
        )


if __name__ == "__main__":
    unittest.main()
