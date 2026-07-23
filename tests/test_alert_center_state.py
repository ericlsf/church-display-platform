import unittest
from unittest.mock import patch

from services.alert_center_state import (
    build_alert_center_state,
)


class AlertCenterStateTests(unittest.TestCase):
    @patch(
        "services.alert_center_state.clear_stale_acknowledgements",
        return_value=[],
    )
    @patch(
        "services.alert_center_state.list_acknowledgements",
        return_value={
            "display:offline": {
                "acknowledged_at": "2026-07-16T12:00:00+00:00",
                "acknowledged_by": "admin",
                "note": "",
            }
        },
    )
    @patch(
        "services.alert_center_state.build_alert_center",
        return_value={
            "alerts": [
                {
                    "key": "display:offline",
                    "severity": "critical",
                    "title": "Display offline",
                },
                {
                    "key": "display:update",
                    "severity": "info",
                    "title": "Update available",
                },
            ],
            "counts": {},
        },
    )
    def test_alerts_are_split(
        self,
        _center,
        _acknowledgements,
        _cleanup,
    ):
        result = build_alert_center_state()

        self.assertEqual(
            len(result["active_alerts"]),
            1,
        )
        self.assertEqual(
            len(result["acknowledged_alerts"]),
            1,
        )
        self.assertEqual(
            result["counts"]["critical"],
            0,
        )


if __name__ == "__main__":
    unittest.main()
