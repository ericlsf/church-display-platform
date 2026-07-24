import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import services.notifications as notifications


class NotificationTests(unittest.TestCase):
    def test_notification_is_not_duplicated(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "notifications.json"
            with patch.object(notifications, "NOTIFICATIONS_FILE", path):
                data = notifications.load_notifications()
                first = notifications._add(
                    data,
                    "job:1",
                    "success",
                    "Done",
                    "Completed",
                )
                second = notifications._add(
                    data,
                    "job:1",
                    "success",
                    "Done",
                    "Completed",
                )

        self.assertIsNotNone(first)
        self.assertIsNone(second)
        self.assertEqual(len(data["notifications"]), 1)

    def test_resolved_job_resolves_matching_notification(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "notifications.json"
            with patch.object(notifications, "NOTIFICATIONS_FILE", path):
                data = notifications.load_notifications()
                notifications._add(
                    data,
                    "job-failed:job-1",
                    "error",
                    "Sync failed",
                    "Network error",
                )
                notifications.save_notifications(data)

                with patch.object(
                    notifications,
                    "list_jobs",
                    return_value=[{
                        "id": "job-1",
                        "status": "failed",
                        "resolved": True,
                        "type": "sync_now",
                    }],
                ), patch.object(
                    notifications,
                    "_pending_displays",
                    return_value=[],
                ), patch.object(
                    notifications,
                    "load_config",
                    return_value={"displays": []},
                ):
                    refreshed = notifications.refresh_notifications()

        self.assertTrue(refreshed["notifications"][0]["resolved"])
        self.assertTrue(refreshed["notifications"][0]["read"])


if __name__ == "__main__":
    unittest.main()
