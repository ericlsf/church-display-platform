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


if __name__ == "__main__":
    unittest.main()
