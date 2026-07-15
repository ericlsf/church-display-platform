import unittest

from services.version_compare import (
    canonical_version,
    versions_match,
)


class VersionCompareTests(unittest.TestCase):
    def test_leading_v_is_ignored(self):
        self.assertTrue(
            versions_match(
                "5.6.2",
                "v5.6.2",
            )
        )

    def test_different_versions_do_not_match(self):
        self.assertFalse(
            versions_match(
                "4.3.0",
                "v5.6.2",
            )
        )

    def test_version_prefix_is_normalized(self):
        self.assertEqual(
            canonical_version("Version v5.6.2"),
            "5.6.2",
        )


if __name__ == "__main__":
    unittest.main()
