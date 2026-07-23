"""Read exact live display data from the heartbeat store."""

from services.heartbeat_store import load_heartbeats
from services.telemetry_normalization import normalize_fleet_telemetry


def heartbeat_records():
    data = load_heartbeats() or {}

    if (
        isinstance(data, dict)
        and isinstance(data.get("heartbeats"), dict)
    ):
        return data["heartbeats"]

    return data if isinstance(data, dict) else {}


def get_live_heartbeat(display_id, display=None):
    records = heartbeat_records()
    display = display or {}

    candidates = [
        display_id,
        str(display_id).replace("-", ""),
        str(display_id).replace("-", "_"),
        display.get("id"),
        display.get("hostname"),
        display.get("name"),
    ]

    for candidate in candidates:
        if candidate and candidate in records:
            return records[candidate]

    wanted = (
        str(display_id or "")
        .lower()
        .replace("-", "")
        .replace("_", "")
        .replace(".", "")
    )

    for record in records.values():
        if not isinstance(record, dict):
            continue

        for value in (
            record.get("id"),
            record.get("hostname"),
            record.get("name"),
        ):
            normalized = (
                str(value or "")
                .lower()
                .replace("-", "")
                .replace("_", "")
                .replace(".", "")
            )

            if normalized == wanted:
                return record

    return {}


def exact_live_telemetry(
    display_id,
    display=None,
    fallback=None,
):
    heartbeat = get_live_heartbeat(
        display_id,
        display,
    )

    source = heartbeat or fallback or {}

    normalized = normalize_fleet_telemetry(
        source,
        display or {},
    )

    media = (
        heartbeat.get("media", {})
        if isinstance(heartbeat, dict)
        else {}
    )
    player = (
        heartbeat.get("player", {})
        if isinstance(heartbeat, dict)
        else {}
    )
    sync = (
        heartbeat.get("sync", {})
        if isinstance(heartbeat, dict)
        else {}
    )

    explicit_count = (
        player.get("media_count")
        if isinstance(player, dict)
        else None
    )

    if explicit_count is None and isinstance(media, dict):
        explicit_count = media.get("total")

    if explicit_count is None and isinstance(sync, dict):
        explicit_count = sync.get("files_synced")

    try:
        if explicit_count is not None:
            normalized["media_count"] = max(
                0,
                int(explicit_count),
            )
    except (TypeError, ValueError):
        pass

    normalized.update({
        "heartbeat_found": bool(heartbeat),
        "heartbeat_version": (
            heartbeat.get("version", "")
            if heartbeat
            else ""
        ),
        "player_media_count": (
            player.get("media_count")
            if isinstance(player, dict)
            else None
        ),
        "media_total": (
            media.get("total")
            if isinstance(media, dict)
            else None
        ),
        "files_synced": (
            sync.get("files_synced")
            if isinstance(sync, dict)
            else None
        ),
        "current_media": (
            player.get("current_media")
            if isinstance(player, dict)
            else ""
        ),
        "received_at": (
            heartbeat.get("received_at", "")
            if heartbeat
            else ""
        ),
    })

    return normalized
