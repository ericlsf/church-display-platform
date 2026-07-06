from datetime import datetime
from flask import Blueprint, render_template
from services.config import load_config, load_hub_settings, load_pending
from services.display_client import get_status, get_sync_status
from services.drive import list_drive_folders
from services.events import read_events

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def dashboard():
    cfg = load_config()
    hub_settings = load_hub_settings()
    pending = load_pending()
    drive_remote = hub_settings.get("drive_remote", "gdrive")
    drive_folders, drive_error = list_drive_folders(drive_remote)
    rows = []
    for display in cfg.get("displays", []):
        status, online = get_status(display)
        sync_status, sync_online = get_sync_status(display)
        current_folder = sync_status.get("folder", "Weekly")
        folder_options = drive_folders
        if current_folder and current_folder not in folder_options:
            folder_options = [current_folder] + folder_options
        rows.append({
            "id": display.get("id", ""),
            "name": display.get("name", "Unnamed Display"),
            "host": display.get("host", ""),
            "online": online,
            "current_media": status.get("current_media", "Unknown"),
            "media_type": status.get("media_type", "Unknown"),
            "overlay": status.get("overlay", ""),
            "countdown": status.get("countdown", ""),
            "last_update": status.get("last_update", "Unknown"),
            "error": status.get("error", ""),
            "sync_online": sync_online,
            "sync_folder": current_folder,
            "sync_state": sync_status.get("state", "unknown"),
            "sync_last_success": sync_status.get("last_success", "Unknown"),
            "folder_options": folder_options,
        })
    return render_template("dashboard.html", rows=rows, now=datetime.now(), active="dashboard", drive_remote=drive_remote, drive_folders=drive_folders, drive_error=drive_error, pending_count=len(pending.get("pending", [])), events=read_events(12))
