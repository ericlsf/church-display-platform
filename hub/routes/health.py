from flask import Blueprint, render_template
from services.config import load_config
from services.display_client import get_status, get_sync_status
from services.events import read_events

health_bp = Blueprint("health", __name__, url_prefix="/health")


@health_bp.route("")
def health():
    cfg = load_config()
    rows = []
    for display in cfg.get("displays", []):
        status, status_ok = get_status(display)
        sync, sync_ok = get_sync_status(display)
        healthy = status_ok and sync_ok
        rows.append({"name": display.get("name", ""), "host": display.get("host", ""), "healthy": healthy, "status_ok": status_ok, "sync_ok": sync_ok, "current_media": status.get("current_media", ""), "last_update": status.get("last_update", ""), "sync_state": sync.get("state", "unknown"), "sync_last_success": sync.get("last_success", "Unknown"), "error": status.get("error") or sync.get("error") or ""})
    return render_template("health.html", rows=rows, events=read_events(100), active="health")
