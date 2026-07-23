import unittest
from unittest.mock import patch

from agent.jobs.sync import handle_sync_now


class SyncGuardTests(unittest.TestCase):
    @patch("agent.jobs.sync.configured_folder", return_value="")
    def test_sync_now_fails_cleanly_without_folder(self, _folder):
        reports = []

        handle_sync_now(
            {"id": "job-1"},
            lambda status, progress, message: reports.append(
                (status, progress, message)
            ),
        )

        self.assertEqual(reports[-1][0], "failed")
        self.assertEqual(reports[-1][1], 100)
        self.assertIn("No playlist folder", reports[-1][2])


if __name__ == "__main__":
    unittest.main()
