from datetime import datetime, timedelta, timezone

from services.audit import read_audit
from services.config import load_config
from services.display_groups import load_groups
from services.display_profiles import load_profiles
from services.fleet_operations import fleet_rows
from services.jobs import list_jobs
from services.config import load_hub_settings
from services.drive import list_drive_folders


def _parse_time(value):
    if not value:
        return None
    value = str(value).strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        result = datetime.fromisoformat(value)
    except ValueError:
        return None
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc)


def display_cards():
    displays = {
        item.get("id"): item
        for item in load_config().get("displays", [])
    }
    rows = fleet_rows()
    jobs = list_jobs(1000)

    pending_counts = {}
    for job in jobs:
        status = str(job.get("status", "")).lower()
        if status not in {
            "queued",
            "pending",
            "running",
            "retrying",
            "in_progress",
        }:
            continue
        display_id = job.get("display_id")
        pending_counts[display_id] = (
            pending_counts.get(display_id, 0) + 1
        )

    cards = []
    for row in rows:
        display_id = row.get("id")
        display = displays.get(display_id, {})
        presentation = display.get("presentation", {})
        overlay = presentation.get("overlay", {})

        cards.append({
            **row,
            "name": display.get("name", row.get("name", display_id)),
            "pending_jobs": pending_counts.get(display_id, 0),
            "profile_name": display.get("profile_name", ""),
            "overlay_text": overlay.get("text", ""),
            "last_sync": (
                row.get("last_sync_at")
                or row.get("last_sync")
                or display.get("last_sync_at")
                or ""
            ),
        })

    return cards


def recent_activity(display_id, minutes=10, limit=50):
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    events = []

    for job in list_jobs(500):
        if job.get("display_id") != display_id:
            continue
        timestamp = (
            job.get("updated_at")
            or job.get("created_at")
        )
        parsed = _parse_time(timestamp)
        if not parsed or parsed < cutoff:
            continue

        events.append({
            "timestamp": timestamp,
            "sort_time": parsed,
            "kind": "job",
            "title": str(
                job.get("type", "job")
            ).replace("_", " ").title(),
            "status": job.get("status", "unknown"),
            "message": job.get("message", ""),
        })

    for row in read_audit(limit=250, query=display_id):
        parsed = _parse_time(row.get("timestamp"))
        if not parsed or parsed < cutoff:
            continue

        events.append({
            "timestamp": row.get("timestamp", ""),
            "sort_time": parsed,
            "kind": "audit",
            "title": str(
                row.get("action", "change")
            ).replace("_", " "),
            "status": row.get("status", "success"),
            "message": row.get("actor", ""),
        })

    events.sort(
        key=lambda event: event["sort_time"],
        reverse=True,
    )

    for event in events:
        event.pop("sort_time", None)

    return events[:limit]


def wizard_options():
    remote = load_hub_settings().get("drive_remote", "gdrive")
    folders, folder_error = list_drive_folders(remote)

    return {
        "groups": load_groups().get("groups", []),
        "profiles": load_profiles().get("profiles", []),
        "folders": folders or [],
        "folder_error": folder_error,
    }
