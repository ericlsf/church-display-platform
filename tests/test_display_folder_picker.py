import unittest
from unittest.mock import patch

from services.display_details import get_display_details


class DisplayFolderPickerTests(unittest.TestCase):
    @patch(
        "services.display_details.list_drive_folders",
        return_value=(["Lobby", "Missions"], ""),
    )
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
        return_value=[
            {
                "id": "welcome-center",
                "assigned_folder": "Missions",
            }
        ],
    )
    @patch(
        "services.display_details.load_hub_settings",
        return_value={"drive_remote": "gdrive"},
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
    def test_current_folder_is_selected_and_listed_once(
        self,
        _config,
        _settings,
        _fleet,
        _groups,
        _profiles,
        _jobs,
        _audit,
        _folders,
    ):
        result = get_display_details("welcome-center")

        self.assertEqual(result["current_folder"], "Missions")
        self.assertEqual(
            result["available_folders"],
            ["Missions", "Lobby"],
        )


if __name__ == "__main__":
    unittest.main()
