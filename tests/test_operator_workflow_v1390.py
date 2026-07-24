from pathlib import Path
from unittest.mock import patch

from services.display_profiles import normalize_settings
from services.operator_workflow import (
    apply_operator_changes,
    normalized_presentation,
)


def test_operator_template_has_one_step_workflow():
    template = Path("hub/templates/display_operator.html").read_text(
        encoding="utf-8"
    )
    assert "Manage Content &amp; Messages" not in template
    assert "Refresh from Drive" in template
    assert "Final full-screen message" in template
    assert "Take over the screen this many seconds before" in template
    assert "Apply Changes to {{ display.name }}" in template
    assert "Image preview unavailable" in template


def test_media_previews_prefer_the_synced_hub_cache():
    route = Path("hub/routes/media.py").read_text(encoding="utf-8")
    assert "cache_path(remote, folder)" in route
    assert "cached_file.is_file()" in route
    assert route.index("cached_file.is_file()") < route.index(
        '["rclone", "cat", source]'
    )


def test_display_cards_link_to_operator_editor():
    template = Path("hub/templates/displays.html").read_text(encoding="utf-8")
    assert "/display/{{ row.id }}/operator" in template
    assert "Manage Content &amp; Messages" in template


def test_images_and_playlists_uses_one_name_everywhere():
    content = Path("hub/templates/content.html").read_text(encoding="utf-8")
    shell = Path("hub/templates/application_shell.html").read_text(
        encoding="utf-8"
    )
    shell_js = Path("hub/static/application-shell.js").read_text(
        encoding="utf-8"
    )
    assert "Images &amp; Playlists - Church Display Hub" in content
    assert "<h1>Images &amp; Playlists</h1>" in content
    assert '("/content", "▥", "Images & Playlists")' in shell
    assert "Advanced Playlist Workflow" not in shell
    assert '["Media Library","Images & Playlists"]' in shell_js


def test_images_and_playlists_keeps_the_everyday_workflow_simple():
    content = Path("hub/templates/content.html").read_text(encoding="utf-8")
    routes = Path("hub/routes/content.py").read_text(encoding="utf-8")

    assert "Choose an image folder" in content
    assert "Arrange playback order" in content
    assert "Save playback order" in content
    assert 'action="/content/save"' in content
    assert "media.media_preview" in content
    assert '@content_bp.route("/save", methods=["POST"])' in routes
    assert "Deploy Now" not in content
    assert "Schedule Deployment" not in content
    assert "Automatic Insertion Policy" not in content
    assert "Recent Content Jobs" not in content
    assert "Save Draft" not in content


def test_simple_content_page_has_responsive_reordering_assets():
    css = Path("hub/static/content-simple-v1390.css").read_text(
        encoding="utf-8"
    )
    javascript = Path("hub/static/content-simple-v1390.js").read_text(
        encoding="utf-8"
    )
    assert "position:sticky" in css
    assert "@media" in css
    assert "dragstart" in javascript
    assert "data-simple-order" in javascript
    assert "event.clientX" in javascript
    assert "drop-before" in javascript
    assert "drop-after" in javascript
    assert ".simple-image-card.drop-before::before" in css


def test_display_player_uses_configurable_takeover_and_service_day():
    player = Path("display/app/main.py").read_text(encoding="utf-8")
    agent = Path("display/agent/jobs/settings.py").read_text(encoding="utf-8")
    assert '"takeover_text"' in player
    assert '"Find your seat"' in player
    assert 'get("takeover_seconds", 30)' in player
    assert 'svc.get("day", "Sunday") != now.strftime("%A")' in player
    assert '"takeover_text"' in agent
    assert '"services"' in agent


def test_presentation_preserves_operator_countdown_fields():
    settings = normalize_settings(
        {
            "countdown": {
                "enabled": True,
                "text": "Gathering begins in",
                "takeover_text": "Please find a seat",
                "start_minutes": 25,
                "takeover_seconds": 45,
                "services": [
                    {"day": "Wednesday", "time": "18:30"},
                ],
            }
        }
    )
    assert settings["countdown"]["text"] == "Gathering begins in"
    assert settings["countdown"]["takeover_text"] == "Please find a seat"
    assert settings["countdown"]["takeover_seconds"] == 45
    assert settings["countdown"]["services"] == [
        {"day": "Wednesday", "time": "18:30"}
    ]


def test_old_displays_receive_clear_operator_defaults():
    settings = normalized_presentation({})
    assert settings["countdown"]["takeover_text"] == "Find your seat"
    assert settings["countdown"]["takeover_seconds"] == 30
    assert len(settings["countdown"]["services"]) == 3


@patch("services.operator_workflow.create_job")
@patch(
    "services.operator_workflow.sync_playlist_from_drive",
    return_value=({"order": ["second.jpg", "first.jpg"]}, ""),
)
@patch("services.operator_workflow.save_playlist_order")
@patch("services.operator_workflow.save_config")
@patch(
    "services.operator_workflow.load_hub_settings",
    return_value={"drive_remote": "gdrive"},
)
@patch(
    "services.operator_workflow.load_config",
    return_value={
        "displays": [
            {
                "id": "welcome-center",
                "name": "Welcome Center",
            }
        ]
    },
)
def test_apply_is_one_operation_that_saves_syncs_and_queues_settings(
    load_config,
    load_settings,
    save_config,
    save_order,
    sync_folder,
    create_job,
):
    save_order.return_value = ["second.jpg", "first.jpg"]
    settings = normalized_presentation({})

    count = apply_operator_changes(
        "welcome-center",
        "Missions",
        ["second.jpg", "first.jpg"],
        settings,
    )

    assert count == 2
    saved = save_config.call_args.args[0]["displays"][0]
    assert saved["assigned_folder"] == "Missions"
    assert saved["presentation"] == settings
    assert [call.args[1] for call in create_job.call_args_list] == [
        "set_sync_folder",
        "apply_display_settings",
    ]
