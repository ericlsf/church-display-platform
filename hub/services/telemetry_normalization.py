"""Normalize live display telemetry from multiple agent generations."""


def _nested(data, *path):
    value = data
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _first(data, paths):
    for path in paths:
        value = _nested(data, *path)
        if value not in (None, ""):
            return value
    return None


def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on", "running", "active", "ok"}:
        return True
    if text in {"0", "false", "no", "off", "stopped", "inactive", "failed"}:
        return False
    return None


def normalize_media_count(health):
    value = _first(health, [
        ("media_count",), ("local_media_count",), ("playlist_count",),
        ("media_files",), ("media", "total"), ("media", "count"),
        ("media", "local_count"), ("player", "media_count"),
        ("playback", "media_count"), ("playlist", "count"),
        ("storage", "media_count"),
    ])
    count = _to_int(value)
    if count is not None:
        return max(0, count)

    current = _first(health, [
        ("current_file",), ("current_media",), ("now_playing",),
        ("player", "current_file"), ("playback", "current_file"),
        ("playback", "current_media"),
    ])
    return 1 if current else 0


def normalize_version(health, configured_version=""):
    live = _first(health, [
        ("version",), ("agent_version",), ("app_version",),
        ("display_version",), ("software_version",), ("release",),
        ("agent", "version"), ("application", "version"),
        ("display_app", "version"), ("heartbeat", "version"),
        ("system", "app_version"),
    ])
    return str(live or configured_version or "unknown").strip() or "unknown"


def normalize_player_running(health):
    value = _first(health, [
        ("display_app_running",), ("player_running",), ("app_running",),
        ("player", "running"), ("display_app", "running"),
        ("services", "player"),
    ])
    parsed = _to_bool(value)
    if parsed is not None:
        return parsed

    current = _first(health, [
        ("current_file",), ("current_media",), ("now_playing",),
        ("player", "current_file"), ("playback", "current_file"),
    ])
    return bool(current)


def normalize_sync_ok(health):
    value = _first(health, [
        ("sync_state",), ("last_sync_status",), ("sync_status",),
        ("sync", "status"), ("media_sync", "status"),
    ])
    return str(value or "").strip().lower() in {
        "success", "succeeded", "complete", "completed", "ok", "healthy",
    }


def normalize_fleet_telemetry(health, display=None):
    display = display or {}
    return {
        "version": normalize_version(health, display.get("version", "")),
        "media_count": normalize_media_count(health),
        "player_running": normalize_player_running(health),
        "sync_ok": normalize_sync_ok(health),
    }
