import unittest
from unittest.mock import patch

from services.display_details import get_display_details


class DisplayDetailsTests(unittest.TestCase):
    @patch("services.display_details.read_audit", return_value=[])
    @patch("services.display_details.list_jobs", return_value=[])
    @patch(
        "services.display_details.load_profiles",
        return_value={"profiles": [], "default_profile_id": ""},
    )
    @patch(
        "services.display_details.load_groups",
        return_value={"groups": []},
    )
    @patch(
        "services.display_details.fleet_rows",
        return_value=[{"id": "welcome-center", "readiness": "ready"}],
    )
    @patch(
        "services.display_details.load_config",
        return_value={
            "displays": [
                {
                    "id": "welcome-center",
                    "name": "Welcome Center",
                }
            ]
        },
    )
    def test_details_are_collected(
        self,
        _config,
        _fleet,
        _groups,
        _profiles,
        _jobs,
        _audit,
    ):
        result = get_display_details("welcome-center")
        self.assertEqual(result["display"]["name"], "Welcome Center")
        self.assertEqual(result["fleet"]["readiness"], "ready")


if __name__ == "__main__":
    unittest.main()
