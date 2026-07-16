import unittest
from unittest.mock import patch
from services.alert_center import build_alert_center

class AlertCenterTests(unittest.TestCase):
    @patch("services.alert_center.list_jobs", return_value=[])
    @patch("services.alert_center.enrich_fleet_rows", side_effect=lambda rows: rows)
    @patch("services.alert_center.fleet_rows", return_value=[{
        "id": "welcome-center",
        "name": "Welcome Center",
        "online": True,
        "health_score": 100,
        "sync_state": "success",
        "sync_folder": "Missions",
        "media_count": 3,
        "version": "6.2.0",
        "update_available": False,
        "system": {"disk": "15%"},
    }])
    def test_healthy_display_has_no_alert(self, _rows, _enrich, _jobs):
        result = build_alert_center()
        self.assertEqual(result["counts"]["total"], 0)

if __name__ == "__main__":
    unittest.main()
