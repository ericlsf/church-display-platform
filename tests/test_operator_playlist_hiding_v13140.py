from pathlib import Path
from unittest.mock import patch

from services.operator_workflow import editor_data


def test_editor_separates_visible_and_hidden_playlist_items():
    config = {
        "displays": [
            {
                "id": "welcome-center",
                "assigned_folder": "Weekly",
            }
        ]
    }
    analysis = {
        "media_items": [
            {"path": "keep.jpg", "name": "Keep"},
            {"path": "hide.jpg", "name": "Hide"},
        ]
    }
    with (
        patch("services.operator_workflow.load_config", return_value=config),
        patch(
            "services.operator_workflow.load_hub_settings",
            return_value={"drive_remote": "gdrive"},
        ),
        patch(
            "services.operator_workflow.cached_drive_folders",
            return_value=(["Weekly"], {}),
        ),
        patch(
            "services.operator_workflow.analyze_cached_folder",
            return_value=analysis,
        ),
        patch(
            "services.operator_workflow.get_playlist_exclusions",
            return_value=["hide.jpg"],
        ),
    ):
        data = editor_data("welcome-center")

    assert [item["path"] for item in data["analysis"]["media_items"]] == [
        "keep.jpg"
    ]
    assert [
        item["path"] for item in data["analysis"]["hidden_media_items"]
    ] == ["hide.jpg"]


def test_everyday_editor_exposes_hide_and_restore_controls():
    template = (
        Path(__file__).parents[1] / "hub" / "templates" / "display_operator.html"
    ).read_text(encoding="utf-8")

    assert 'name="playlist_excluded"' in template
    assert "data-hide-media" in template
    assert "data-restore-media" in template
    assert "without deleting it from Google Drive" in template
