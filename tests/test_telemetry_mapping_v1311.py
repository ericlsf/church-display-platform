from services.telemetry_normalization import normalize_media_count


def test_welcome_center_status_payload_reports_media_count():
    status = {
        "current_media": "Copy of Lifespring Kids Slide.jpg",
        "player_media_count": 3,
        "images": 3,
        "videos": 0,
        "total_media": 3,
        "memory": "11%",
        "disk": "15%",
    }
    assert normalize_media_count(status) == 3


def test_heartbeat_media_payload_reports_total_count():
    heartbeat = {
        "player": {"current_media": "slide.jpg", "media_count": 3},
        "media": {"images": 3, "videos": 0, "total": 3},
    }
    assert normalize_media_count(heartbeat) == 3


def test_displays_route_accepts_current_agent_system_keys():
    from pathlib import Path

    route = (Path(__file__).resolve().parents[1] / "hub/routes/displays.py").read_text()
    assert '"storage_usage", "disk"' in route
    assert '"ram_usage", "memory"' in route
