import hashlib
import json
from datetime import datetime, timezone

from services.config import CONFIG_DIR, load_pending
from services.fleet_state import build_fleet_state
from services.jobs import list_jobs
from services.resilience import load_resilience

DISMISSALS_FILE = CONFIG_DIR / "notification_dismissals.json"


def _load_dismissals():
    try:
        data = json.loads(DISMISSALS_FILE.read_text())
    except Exception:
        data = {"dismissed": []}
    data.setdefault("dismissed", [])
    return set(data["dismissed"])


def _save_dismissals(values):
    DISMISSALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = DISMISSALS_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps({"dismissed": sorted(values)}, indent=2))
    tmp.replace(DISMISSALS_FILE)


def fingerprint(kind, key, message):
    raw = f"{kind}|{key}|{message}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:20]


def dismiss(notification_id):
    values = _load_dismissals()
    values.add(notification_id)
    _save_dismissals(values)


def clear_dismissals():
    _save_dismissals(set())


def build_notifications(include_dismissed=False):
    state = build_fleet_state()
    dismissed = _load_dismissals()
    items = []

    def add(kind, level, title, message, key, href=""):
        item_id = fingerprint(kind, key, message)
        item = {
            "id": item_id,
            "kind": kind,
            "level": level,
            "title": title,
            "message": message,
            "href": href,
            "dismissed": item_id in dismissed,
        }
        if include_dismissed or not item["dismissed"]:
            items.append(item)

    resilience = load_resilience()
    if resilience.get("maintenance", {}).get("enabled"):
        add("maintenance", "warning", "Maintenance mode enabled", resilience["maintenance"].get("message", "Maintenance in progress"), "global", "/resilience")

    for row in state.get("rows", []):
        display_id = row.get("id", "")
        name = row.get("name", display_id or "Display")
        if not row.get("online"):
            add("display_offline", "danger", "Display offline", f"{name} is offline.", display_id, "/operations")
        if str(row.get("sync_state", "")).lower() in {"error", "failed"}:
            add("sync_failed", "danger", "Sync failed", f"{name} is reporting a sync failure.", display_id, "/jobs")
        if row.get("update_available"):
            add("update_available", "warning", "Update available", f"{name} can be updated to {row.get('latest_tag')}.", display_id, "/deployments")
        if row.get("git", {}).get("dirty") == "yes":
            add("dirty_tree", "warning", "Uncommitted changes", f"{name} has uncommitted local changes.", display_id, "/system")

    pending_count = len(load_pending().get("pending", []))
    if pending_count:
        add("pending_enrollment", "warning", "Pending enrollment", f"{pending_count} display(s) are waiting for approval.", str(pending_count), "/setup")

    for job in list_jobs(100):
        if job.get("status") == "failed":
            add(
                "job_failed",
                "danger",
                "Job failed",
                f"{job.get('type')} for {job.get('display_id')}: {job.get('message') or 'No details'}",
                job.get("id", ""),
                "/jobs",
            )

    priority = {"danger": 0, "warning": 1, "info": 2}
    items.sort(key=lambda item: (priority.get(item["level"], 9), item["title"], item["message"]))
    return items


def notification_summary():
    items = build_notifications()
    return {
        "total": len(items),
        "danger": sum(1 for item in items if item["level"] == "danger"),
        "warning": sum(1 for item in items if item["level"] == "warning"),
    }
