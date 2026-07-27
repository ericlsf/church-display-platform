from pathlib import Path
from unittest.mock import patch

from flask import Flask

from routes.content import content_page


def test_hidden_media_keeps_its_master_playlist_position():
    app = Flask(__name__)
    analysis = {
        "media_items": [
            {"path": "first.jpg", "name": "First", "type": "image"},
            {"path": "second.jpg", "name": "Second", "type": "image"},
            {"path": "third.jpg", "name": "Third", "type": "image"},
        ],
        "playlist_order": ["first.jpg", "second.jpg", "third.jpg"],
    }
    workflow = {
        "published_order": ["third.jpg", "second.jpg", "first.jpg"],
        "draft_excluded": ["second.jpg"],
    }

    with (
        app.test_request_context("/content?folder=Weekly"),
        patch("routes.content.load_hub_settings", return_value={"drive_remote": "gdrive"}),
        patch("routes.content.list_drive_folders", return_value=(["Weekly"], "")),
        patch("routes.content.current_analysis", return_value=analysis),
        patch("routes.content.get_playlist_entry", return_value=workflow),
        patch("routes.content.displays_using_folder", return_value=[]),
        patch("routes.content.render_template", side_effect=lambda _name, **context: context),
    ):
        context = content_page()

    result = context["analysis"]
    assert result["playlist_master_order"] == [
        "third.jpg",
        "second.jpg",
        "first.jpg",
    ]
    assert [item["path"] for item in result["media_items"]] == [
        "third.jpg",
        "first.jpg",
    ]
    assert result["hidden_media_items"][0]["path"] == "second.jpg"
    assert result["hidden_media_items"][0]["playlist_position"] == 1


def test_hidden_media_has_previews_and_restore_does_not_auto_publish():
    template = Path("hub/templates/content.html").read_text(encoding="utf-8")
    javascript = Path("hub/static/content-simple-v1390.js").read_text(
        encoding="utf-8"
    )
    css = Path("hub/static/content-shared-playlist-v13151.css").read_text(
        encoding="utf-8"
    )

    assert "simple-hidden-preview" in template
    assert 'data-position="{{ item.playlist_position }}"' in template
    assert "playlist_master_order" in template
    assert "insertRestoredCard" in javascript
    assert "requestSubmit" not in javascript
    assert "grid-template-columns: repeat(auto-fill, minmax(180px, 1fr))" in css
    assert ".simple-hidden-card" in css
