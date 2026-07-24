from services.config import load_config, load_hub_settings, save_config
from services.content_cache import sync_playlist_from_drive
from services.jobs import create_job
from services.media import save_playlist_order
from services.media_index import analyze_cached_folder, cached_drive_folders


DEFAULT_SERVICES = [
    {"day": "Sunday", "time": "08:00"},
    {"day": "Sunday", "time": "09:30"},
    {"day": "Sunday", "time": "11:15"},
]


def _bounded_int(value, default, minimum, maximum):
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


def _display(config, display_id):
    display = next(
        (
            item
            for item in config.get("displays", [])
            if item.get("id") == display_id
        ),
        None,
    )
    if not display:
        raise ValueError("Display not found")
    return display


def normalized_presentation(display):
    raw = display.get("presentation", {})
    countdown = raw.get("countdown", {})
    services = countdown.get("services") or DEFAULT_SERVICES
    return {
        "overlay": {
            "enabled": bool(raw.get("overlay", {}).get("enabled", True)),
            "text": str(raw.get("overlay", {}).get("text", "Welcome")),
        },
        "clock": {
            "enabled": bool(raw.get("clock", {}).get("enabled", True)),
        },
        "countdown": {
            "enabled": bool(countdown.get("enabled", True)),
            "text": str(countdown.get("text", "Service starts in")),
            "takeover_text": str(
                countdown.get("takeover_text", "Find your seat")
            ),
            "start_minutes": _bounded_int(
                countdown.get("start_minutes"), 20, 0, 180
            ),
            "takeover_seconds": _bounded_int(
                countdown.get("takeover_seconds"), 30, 0, 300
            ),
            "services": [
                {
                    "day": str(row.get("day", "Sunday")),
                    "time": str(row.get("time", "")),
                }
                for row in services
                if row.get("time")
            ],
        },
        "timings": {
            "image_duration": _bounded_int(
                raw.get("timings", {}).get("image_duration"),
                8,
                1,
                300,
            ),
        },
    }


def editor_data(display_id, selected_folder=""):
    config = load_config()
    display = _display(config, display_id)
    remote = load_hub_settings().get("drive_remote", "gdrive")
    folders, media_index = cached_drive_folders(remote)
    current_folder = (
        display.get("assigned_folder")
        or display.get("sync_folder")
        or ""
    )
    folder = (selected_folder or current_folder).strip().strip("/")
    if current_folder and current_folder not in folders:
        folders.insert(0, current_folder)
    analysis = (
        analyze_cached_folder(
            remote,
            folder,
            recursive=False,
            supported_only=True,
        )
        if folder
        else None
    )
    return {
        "display": display,
        "remote": remote,
        "folders": folders,
        "folder": folder,
        "current_folder": current_folder,
        "analysis": analysis,
        "presentation": normalized_presentation(display),
        "media_index": media_index,
    }


def apply_operator_changes(display_id, folder, order, settings):
    config = load_config()
    display = _display(config, display_id)
    remote = load_hub_settings().get("drive_remote", "gdrive")
    folder = (folder or "").strip().strip("/")
    if not folder:
        raise ValueError("Choose a Google Drive folder")

    order = save_playlist_order(remote, folder, order)
    manifest, error = sync_playlist_from_drive(remote, folder)
    if error:
        raise RuntimeError(f"Google Drive sync failed: {error}")

    final_order = manifest.get("order") or order
    display["assigned_folder"] = folder
    display["sync_folder"] = folder
    display["sync_remote"] = remote
    display["presentation"] = settings
    save_config(config)

    create_job(
        display_id,
        "set_sync_folder",
        {
            "remote": remote,
            "folder": folder,
            "run_now": True,
            "source": "operator_workflow",
            "playlist_order": final_order,
        },
    )
    create_job(
        display_id,
        "apply_display_settings",
        {"settings": settings},
    )
    return len(final_order)
