"""Enrich fleet rows with authoritative raw-heartbeat values."""
from services.live_display_telemetry import exact_live_telemetry

def enrich_fleet_row(row):
    row = dict(row or {})
    display_id = row.get("id")
    if not display_id:
        return row

    telemetry = exact_live_telemetry(
        display_id,
        display=row,
        fallback=row,
    )

    try:
        count = max(0, int(telemetry.get("media_count") or 0))
    except (TypeError, ValueError):
        count = 0

    row.update({
        "media_count": count,
        "version": (
            telemetry.get("heartbeat_version")
            or telemetry.get("version")
            or row.get("version")
            or "unknown"
        ),
        "heartbeat_version": telemetry.get("heartbeat_version", ""),
        "player_media_count": telemetry.get("player_media_count"),
        "media_total": telemetry.get("media_total"),
        "files_synced": telemetry.get("files_synced"),
        "current_media": (
            telemetry.get("current_media")
            or row.get("current_media")
            or ""
        ),
        "heartbeat_received_at": telemetry.get("received_at", ""),
    })
    return row

def enrich_fleet_rows(rows):
    return [enrich_fleet_row(row) for row in rows]
