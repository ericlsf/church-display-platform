import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from services.alert_policy import apply_alert_policy


class AlertPolicyTests(unittest.TestCase):
    @patch(
        "services.alert_policy.load_alert_rules",
        return_value={
            "quiet_hours_enabled": True,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "07:00",
            "categories": {
                "health": True,
                "software": False,
            },
        },
    )
    def test_quiet_hours_suppress_noncritical(
        self,
        _rules,
    ):
        result = apply_alert_policy(
            {
                "alerts": [
                    {
                        "key": "health",
                        "severity": "warning",
                        "category": "health",
                    },
                    {
                        "key": "critical",
                        "severity": "critical",
                        "category": "health",
                    },
                    {
                        "key": "update",
                        "severity": "info",
                        "category": "software",
                    },
                ]
            },
            now=datetime(
                2026,
                7,
                16,
                23,
                0,
                tzinfo=timezone.utc,
            ),
        )

        self.assertEqual(
            result["counts"]["active"],
            1,
        )
        self.assertEqual(
            result["counts"]["suppressed"],
            2,
        )


if __name__ == "__main__":
    unittest.main()
