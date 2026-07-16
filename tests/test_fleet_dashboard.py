import unittest
from unittest.mock import patch

from services.fleet_dashboard import (
    build_fleet_dashboard,
)


class FleetDashboardTests(unittest.TestCase):
    @patch(
        "services.fleet_dashboard.list_jobs",
        return_value=[],
    )
    @patch(
        "services.fleet_dashboard.fleet_rows",
        return_value=[
            {
                "id": "welcome-center",
                "name": "Welcome Center",
                "online": True,
                "health_score": 100,
                "version": "6.0.0",
                "sync_state": "success",
                "sync_folder": "Missions",
                "update_available": False,
            },
            {
                "id": "lobby",
                "name": "Lobby",
                "online": False,
                "health_score": 40,
                "version": "5.9.3",
                "sync_state": "failed",
                "sync_folder": "Weekly",
                "update_available": True,
            },
        ],
    )
    def test_metrics_and_attention(
        self,
        _rows,
        _jobs,
    ):
        result = build_fleet_dashboard()

        self.assertEqual(
            result["metrics"]["total"],
            2,
        )
        self.assertEqual(
            result["metrics"]["offline"],
            1,
        )
        self.assertEqual(
            len(result["attention"]),
            1,
        )


if __name__ == "__main__":
    unittest.main()
