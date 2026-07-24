import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from services.config import load_config
from services.jobs import list_jobs


ROOT = Path(__file__).resolve().parents[2]
NOTIFICATIONS_FILE = ROOT / "hub" / "config" / "notifications.json"
PENDING_FILE = ROOT / "hub" / "config" / "pending_displays.json"

PROBLEM_JOB_STATUSES = {"failed", "timed_out", "cancelled"}
SUCCESS_JOB_TYPES = {
    "deploy_update",
    "set_sync_folder",
    "sync_now",
    "restart_display",
    "apply_display_settings",
}


def _now():
    return datetime.now(timezone.utc).isoformat()


def load_notifications():
    if not NOTIFICATIONS_FILE.exists():
        return {"notifications": [], "seen_sources": []}
    try:
        data = json.loads(NOTIFICATIONS_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = {"notifications": [], "seen_sources": []}
    data.setdefault("notifications", [])
    data.setdefault("seen_sources", [])
    return data


def save_notifications(data):
    NOTIFICATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp = NOTIFICATIONS_FILE.with_suffix(".json.tmp")
    temp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    temp.replace(NOTIFICATIONS_FILE)


def _add(data, source_key, level, title, message, target="", link=""):
    if source_key in data["seen_sources"]:
        return None

    item = {
        "id": str(uuid.uuid4()),
        "source_key": source_key,
        "level": level,
        "title": title,
        "message": message,
        "target": target,
        "link": link,
        "created_at": _now(),
        "read": False,
        "dismissed": False,
        "resolved": False,
    }
    data["notifications"].append(item)
    data["seen_sources"].append(source_key)
    return item


def _pending_displays():
    if not PENDING_FILE.exists():
        return []
    try:
        data = json.loads(PENDING_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []
    return data.get("pending", [])


def refresh_notifications():
    data = load_notifications()
    changed = False

    for pending in _pending_displays():
        source_key = f"pending:{pending.get('requested_id') or pending.get('host')}"
        item = _add(
            data,
            source_key,
            "info",
            "Display awaiting approval",
            (
                f"{pending.get('name', 'New display')} is waiting "
                "for enrollment approval."
            ),
            target=pending.get("requested_id", ""),
            link="/setup",
        )
        changed = changed or bool(item)

    for job in list_jobs(500):
        job_id = job.get("id")
        status = str(job.get("status", "")).lower()
        job_type = job.get("type", "job")
        display_id = job.get("display_id", "")
        message = job.get("message", "")

        if job.get("resolved") or job.get("acknowledged"):
            source_key = f"job-failed:{job_id}"
            for existing in data["notifications"]:
                if existing.get("source_key") == source_key:
                    existing["resolved"] = True
                    existing["read"] = True
                    changed = True

        if status in PROBLEM_JOB_STATUSES:
            item = _add(
                data,
                f"job-failed:{job_id}",
                "error",
                f"{job_type.replace('_', ' ').title()} failed",
                message or f"Job failed for {display_id}.",
                target=display_id,
                link="/errors",
            )
            changed = changed or bool(item)
        elif status == "success" and job_type in SUCCESS_JOB_TYPES:
            item = _add(
                data,
                f"job-success:{job_id}",
                "success",
                f"{job_type.replace('_', ' ').title()} completed",
                message or f"Job completed for {display_id}.",
                target=display_id,
                link="/jobs",
            )
            changed = changed or bool(item)

    config = load_config()
    for display in config.get("displays", []):
        display_id = display.get("id", "")
        if display.get("maintenance", {}).get("enabled"):
            continue
        if display.get("online") is False:
            item = _add(
                data,
                f"display-offline:{display_id}",
                "warning",
                "Display offline",
                f"{display.get('name', display_id)} is offline.",
                target=display_id,
                link="/operations-center",
            )
            changed = changed or bool(item)

    if changed:
        save_notifications(data)

    return data


def visible_notifications(limit=100):
    data = refresh_notifications()
    rows = [
        item
        for item in data["notifications"]
        if not item.get("dismissed")
    ]
    rows.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return rows[:limit]


def unread_count():
    return sum(
        1
        for item in visible_notifications(1000)
        if not item.get("read")
    )


def mark_read(notification_id=None, all_notifications=False):
    data = load_notifications()
    for item in data["notifications"]:
        if all_notifications or item.get("id") == notification_id:
            item["read"] = True
    save_notifications(data)


def dismiss(notification_id):
    data = load_notifications()
    for item in data["notifications"]:
        if item.get("id") == notification_id:
            item["dismissed"] = True
            item["read"] = True
            break
    save_notifications(data)


def clear_resolved():
    data = load_notifications()
    for item in data["notifications"]:
        if item.get("resolved") or item.get("level") == "success":
            item["dismissed"] = True
            item["read"] = True
    save_notifications(data)


def resolve_notification(notification_id):
    data = load_notifications()
    for item in data["notifications"]:
        if item.get("id") == notification_id:
            item["resolved"] = True
            item["read"] = True
            break
    save_notifications(data)


# ---------------------------------------------------------------------------
# Backward-compatible dashboard API
# ---------------------------------------------------------------------------

def build_notifications(limit=100, *args, **kwargs):
    """
    Compatibility wrapper for dashboard code written before the
    Notification Center service was introduced.
    """
    try:
        return visible_notifications(limit=int(limit or 100))
    except (TypeError, ValueError):
        return visible_notifications(limit=100)


def notification_summary(*args, **kwargs):
    """
    Return notification totals in the format expected by older dashboard
    routes and templates.
    """
    rows = visible_notifications(limit=1000)

    unread = sum(
        1
        for item in rows
        if not item.get("read")
    )

    errors = sum(
        1
        for item in rows
        if item.get("level") == "error"
    )

    warnings = sum(
        1
        for item in rows
        if item.get("level") == "warning"
    )

    return {
        "total": len(rows),
        "unread": unread,
        "errors": errors,
        "warnings": warnings,
        "items": rows[:5],
        "notifications": rows[:5],
    }
