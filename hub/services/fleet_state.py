from pathlib import Path

from services.config import load_config, load_hub_settings, load_pending
from services.display_client import get_status, get_sync_status
from services.drive import list_drive_folders
from services.events import read_event_records, read_events
from services.heartbeat_store import load_heartbeats, get_heartbeat_for_display
from services.jobs import list_jobs
from services.releases import latest_git_tag
from services.timeutil import human_age, is_fresh, seconds_old


PREVIEW_DIR = Path(__file__).resolve().parent.parent / "static" / "previews"


def useful_value(*values):
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and value.strip().lower() in {"", "unknown", "n/a", "none", "null", "—"}:
            continue
        return value
    return None


def media_count_for(status, heartbeat):
    hb_media = heartbeat.get("media") or {}
    hb_player = heartbeat.get("player") or {}
    candidates = [
        status.get("total_media"),
        status.get("media_count"),
        status.get("player_media_count"),
        hb_media.get("total"),
        hb_player.get("media_count"),
        heartbeat.get("total_media"),
        heartbeat.get("media_count"),
    ]

    for value in candidates:
        try:
            if int(value) > 0:
                return int(value)
        except (TypeError, ValueError):
            continue

    for value in candidates:
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return 0


def system_health_for(status, heartbeat):
    hb_system = heartbeat.get("system") or {}
    status_system = status.get("system") or {}

    return {
        "cpu_temp": useful_value(
            hb_system.get("cpu_temp"),
            heartbeat.get("cpu_temp"),
            status_system.get("cpu_temp"),
            status.get("cpu_temp"),
        ) or "Unknown",
        "memory": useful_value(
            status.get("memory"),
            status_system.get("memory"),
            hb_system.get("memory"),
            heartbeat.get("memory"),
            heartbeat.get("memory_usage"),
        ) or "Unknown",
        "disk": useful_value(
            status.get("disk"),
            status_system.get("disk"),
            hb_system.get("disk"),
            heartbeat.get("disk"),
            heartbeat.get("disk_usage"),
        ) or "Unknown",
        "uptime": useful_value(
            status.get("uptime"),
            status_system.get("uptime"),
            hb_system.get("uptime"),
            heartbeat.get("uptime"),
        ) or "Unknown",
    }


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


def health_state_for(online, system, active_job=None):
    if active_job and active_job.get("type") == "deploy_update":
        return "updating"
    if not online:
        return "offline"
    for key in ("memory", "disk"):
        value = str(system.get(key, "")).replace("%", "").strip()
        try:
            if float(value) >= 90:
                return "warning"
        except ValueError:
            pass
    return "online"


def build_fleet_state():
    cfg = load_config()
    hub_settings = load_hub_settings()
    pending = load_pending()
    heartbeats = load_heartbeats().get("heartbeats", {})

    drive_remote = hub_settings.get("drive_remote", "gdrive")
    drive_folders, drive_error = list_drive_folders(drive_remote)
    latest_tag = latest_git_tag()
    active_jobs = {}
    for job in list_jobs(500):
        if job.get("status") not in {"queued", "running"}:
            continue
        active_jobs.setdefault(job.get("display_id"), job)

    rows = []

    for display in cfg.get("displays", []):
        status, status_online = get_status(display)
        sync_status, sync_online = get_sync_status(display)
        hb = get_heartbeat_for_display(display, heartbeats)

        hb_player = hb.get("player", {})
        hb_sync = hb.get("sync", {})
        hb_git = hb.get("git", {})

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
        system = system_health_for(status, hb)
        online = bool(status_online or heartbeat_fresh)
        active_job = active_jobs.get(display_id)

        rows.append({
            "id": display_id,
            "name": display.get("name", "Unnamed Display"),
            "host": display.get("host", ""),
            "group": display.get("group", ""),
            "online": online,
            "health_state": health_state_for(online, system, active_job),
            "active_job": active_job or {},
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
            "media_count": media_count_for(status, hb),
            "overlay": status.get("overlay") or hb_player.get("overlay") or "",
            "countdown": status.get("countdown") or hb_player.get("countdown") or "",
            "last_update": status.get("last_update") or hb_player.get("last_update") or "Unknown",
            "error": status.get("error", ""),
            "sync_folder": current_folder,
            "sync_state": sync_status.get("state") or hb_sync.get("state") or "unknown",
            "sync_last_success": sync_status.get("last_success") or hb_sync.get("last_success") or "Unknown",
            "folder_options": folder_options,
            "system": system,
            "preview_url": preview_url_for(display_id),
        })

    outdated_rows = [row for row in rows if row.get("update_available")]

    alerts = build_alerts(rows, drive_error)
    event_records = read_event_records(30)
    recent_outcomes = [
        {
            "level": event.get("level", "info"),
            "message": event.get("message", ""),
        }
        for event in event_records
        if event.get("level") in {"success", "danger"}
    ][:5]
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
        "event_records": event_records,
        "alerts": alerts,
        "notifications": [
            {
                "level": alert.get("level", "warning"),
                "message": alert.get("message", ""),
            }
            for alert in alerts
        ] + recent_outcomes,
    }
