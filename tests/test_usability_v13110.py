from unittest.mock import patch

from hub.services import fleet_dashboard, media


def test_playlist_exclusions_filter_media(tmp_path):
    playlist_file = tmp_path / "playlists.json"
    with patch.object(media, "PLAYLISTS_FILE", playlist_file):
        media.save_playlist_order("gdrive", "Events", ["one.jpg", "two.jpg"])
        media.save_playlist_exclusions("gdrive", "Events", ["two.jpg"], draft=False)
        items = [
            {"path": "one.jpg", "name": "one.jpg", "supported": True, "is_dir": False},
            {"path": "two.jpg", "name": "two.jpg", "supported": True, "is_dir": False},
        ]
        assert [item["path"] for item in media.ordered_media_items(
            items,
            media.get_playlist_order("gdrive", "Events"),
            media.get_playlist_exclusions("gdrive", "Events"),
        )] == ["one.jpg"]


def test_publish_carries_hidden_items(tmp_path):
    playlist_file = tmp_path / "playlists.json"
    with patch.object(media, "PLAYLISTS_FILE", playlist_file):
        media.save_playlist_draft("gdrive", "Events", ["one.jpg"])
        media.save_playlist_exclusions("gdrive", "Events", ["two.jpg"], draft=True)
        media.publish_playlist("gdrive", "Events")
        entry = media.get_playlist_entry("gdrive", "Events")
        assert entry["published_excluded"] == ["two.jpg"]


def test_dashboard_deduplicates_sync_issue():
    row = {
        "id": "lobby",
        "name": "Lobby",
        "online": True,
        "health_score": 80,
        "checks": {"online": True, "player": True, "playlist": True, "media": True, "sync": False},
        "device_role": "player",
        "sync_state": "unknown",
        "update_available": False,
    }
    with patch.object(fleet_dashboard, "fleet_rows", return_value=[row]), patch.object(
        fleet_dashboard, "list_jobs", return_value=[]
    ):
        dashboard = fleet_dashboard.build_fleet_dashboard()
    assert [issue["key"] for issue in dashboard["attention"][0]["issues"]] == ["sync"]
