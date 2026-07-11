from pathlib import Path

from services.config import load_config, load_hub_settings, load_pending
from services.display_client import get_status, get_sync_status
from services.drive import list_drive_folders
from services.events import read_events
from services.heartbeat_store import load_heartbeats, get_heartbeat_for_display
from services.releases import latest_git_tag
from services.timeutil import human_age, is_fresh, seconds_old


PREVIEW_DIR = Path(__file__).resolve().parent.parent / "static" / "previews"


def preview_url_for(display_id):
    path = PREVIEW_DIR / f"{display_id}.jpg"
    if path.exists():
        return f"/static/previews/{display_id}.jpg?ts={int(path.stat().st_mtime)}"
    return ""


def build_alerts(rows, drive_error=""):
    alerts = []

    if drive_error:
        alerts.append({"level": "warning", "message": f"Google Drive folder lookup failed: {drive_error}"})

    for row in rows:
        name = row.get("name", "Display")

        if not row.get("online"):
            alerts.append({"level": "danger", "message": f"{name} appears offline or has no recent heartbeat."})

        hb_age = row.get("heartbeat_age_seconds")
        if hb_age is not None and hb_age > 120:
            alerts.append({"level": "warning", "message": f"{name} heartbeat is stale ({row.get('heartbeat_age')})."})

        if str(row.get("sync_state", "")).lower() == "error":
            alerts.append({"level": "danger", "message": f"{name} sync is reporting an error."})

        if row.get("git", {}).get("dirty") == "yes":
            alerts.append({"level": "warning", "message": f"{name} has uncommitted local changes."})

        if row.get("heartbeat_fresh") and not row.get("display_app_running"):
            alerts.append({
                "level": "danger",
                "message": f"{name} display app is not running.",
                "display_id": row.get("id"),
                "action": "restart_display",
            })

        temp = str(row.get("system", {}).get("cpu_temp", ""))
        try:
            temp_value = float(temp.replace("°C", "").strip())
            if temp_value >= 75:
                alerts.append({"level": "danger", "message": f"{name} CPU temperature is high: {temp}."})
            elif temp_value >= 65:
                alerts.append({"level": "warning", "message": f"{name} CPU temperature is elevated: {temp}."})
        except Exception:
            pass

    return alerts


def build_fleet_state():
    cfg = load_config()
    hub_settings = load_hub_settings()
    pending = load_pending()
    heartbeats = load_heartbeats().get("heartbeats", {})

    drive_remote = hub_settings.get("drive_remote", "gdrive")
    drive_folders, drive_error = list_drive_folders(drive_remote)
    latest_tag = latest_git_tag()

    rows = []

    for display in cfg.get("displays", []):
        status, status_online = get_status(display)
        sync_status, sync_online = get_sync_status(display)
        hb = get_heartbeat_for_display(display, heartbeats)

        hb_player = hb.get("player", {})
        hb_sync = hb.get("sync", {})
        hb_system = hb.get("system", {})
        hb_git = hb.get("git", {})
        hb_display_app = hb.get("display_app", {})

        heartbeat_received_at = hb.get("received_at", "")
        heartbeat_fresh = is_fresh(heartbeat_received_at, 90)
        heartbeat_age_seconds = seconds_old(heartbeat_received_at)

        current_folder = sync_status.get("folder") or hb_sync.get("folder") or "Weekly"

        folder_options = list(drive_folders)
        if current_folder and current_folder not in folder_options:
            folder_options = [current_folder] + folder_options

        display_id = display.get("id", "")
        current_tag = hb_git.get("tag") or "Unknown"
        update_available = bool(latest_tag and current_tag not in [latest_tag, "Unknown", "untagged", ""])

        rows.append({
            "id": display_id,
            "name": display.get("name", "Unnamed Display"),
            "host": display.get("host", ""),
            "group": display.get("group", ""),
            "online": bool(status_online or heartbeat_fresh),
            "status_online": status_online,
            "sync_online": sync_online,
            "heartbeat_fresh": heartbeat_fresh,
            "heartbeat": human_age(heartbeat_received_at),
            "heartbeat_raw": heartbeat_received_at,
            "heartbeat_age": human_age(heartbeat_received_at),
            "heartbeat_age_seconds": heartbeat_age_seconds,
            "version": hb.get("version", "Unknown"),
            "git": hb_git,
            "current_tag": current_tag,
            "latest_tag": latest_tag or "Unknown",
            "update_available": update_available,
            "config_version": hb.get("config_version", "Unknown"),
            "current_media": status.get("current_media") or hb_player.get("current_media") or "Unknown",
            "media_type": status.get("media_type") or hb_player.get("media_type") or "Unknown",
            "overlay": status.get("overlay") or hb_player.get("overlay") or "",
            "countdown": status.get("countdown") or hb_player.get("countdown") or "",
            "last_update": status.get("last_update") or hb_player.get("last_update") or "Unknown",
            "error": status.get("error", ""),
            "sync_folder": current_folder,
            "sync_state": sync_status.get("state") or hb_sync.get("state") or "unknown",
            "sync_last_success": sync_status.get("last_success") or hb_sync.get("last_success") or "Unknown",
            "folder_options": folder_options,
            "system": hb_system,
            "display_app": hb_display_app,
            "display_app_running": bool(hb_display_app.get("running")),
            "display_app_state": hb_display_app.get("active_state", "unknown"),
            "preview_url": preview_url_for(display_id),
        })

    outdated_rows = [row for row in rows if row.get("update_available")]

    return {
        "rows": rows,
        "outdated_rows": outdated_rows,
        "outdated_count": len(outdated_rows),
        "drive_remote": drive_remote,
        "drive_folders": drive_folders,
        "drive_error": drive_error,
        "latest_tag": latest_tag or "",
        "pending_count": len(pending.get("pending", [])),
        "events": read_events(12),
        "alerts": build_alerts(rows, drive_error),
    }
