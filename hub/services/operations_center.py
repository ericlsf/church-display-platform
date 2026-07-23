from services.config import load_config, load_hub_settings, save_config
from services.content_cache import sync_playlist_from_drive
from services.drive import list_drive_folders
from services.fleet_operations import fleet_rows
from services.jobs import create_job, list_jobs
from services.releases import latest_git_tag

PROBLEM_STATUSES = {"failed", "timed_out", "cancelled"}
ACTIVE_STATUSES = {"queued", "pending", "running", "retrying", "in_progress"}

def dashboard_data():
    rows = fleet_rows()
    jobs = list_jobs(250)
    summary = {
        "total": len(rows),
        "ready": sum(1 for r in rows if r.get("readiness") == "ready"),
        "offline": sum(1 for r in rows if r.get("readiness") == "offline"),
        "attention": sum(1 for r in rows if r.get("readiness") in {"needs_attention", "needs_playlist"}),
        "provisioning": sum(1 for r in rows if r.get("readiness") == "provisioning"),
        "running_jobs": sum(1 for j in jobs if str(j.get("status", "")).lower() in ACTIVE_STATUSES),
        "failed_jobs": sum(1 for j in jobs if str(j.get("status", "")).lower() in PROBLEM_STATUSES and not j.get("resolved")),
    }
    remote = load_hub_settings().get("drive_remote", "gdrive")
    folders, folder_error = list_drive_folders(remote)
    return {
        "rows": rows,
        "summary": summary,
        "attention_rows": [r for r in rows if r.get("readiness") != "ready"],
        "recent_jobs": jobs[:12],
        "folders": folders,
        "folder_error": folder_error,
        "latest_tag": latest_git_tag(),
    }

def update_display_quick_settings(display_id, folder, overlay_text, overlay_enabled=True):
    cfg = load_config()
    display = next((d for d in cfg.get("displays", []) if d.get("id") == display_id), None)
    if not display:
        raise ValueError("Display not found")
    remote = load_hub_settings().get("drive_remote", "gdrive")
    folder = (folder or "").strip().strip("/")
    overlay_text = (overlay_text or "").strip()[:160]

    if folder and folder != (display.get("assigned_folder") or ""):
        manifest, error = sync_playlist_from_drive(remote, folder)
        if error:
            raise RuntimeError(error)
        display["assigned_folder"] = folder
        create_job(display_id, "set_sync_folder", {
            "remote": remote,
            "folder": folder,
            "run_now": True,
            "source": "hub",
            "playlist_order": manifest.get("order", []),
        })

    presentation = display.setdefault("presentation", {})
    presentation.setdefault("clock", {"enabled": True})
    presentation.setdefault("countdown", {"enabled": True, "start_minutes": 20})
    presentation.setdefault("timings", {"image_duration": 8})
    presentation["overlay"] = {"enabled": bool(overlay_enabled), "text": overlay_text}

    create_job(display_id, "apply_display_settings", {"settings": presentation})
    save_config(cfg)

def retry_contextual_action(display_id, action):
    if action == "sync":
        return create_job(display_id, "sync_now", {})
    if action == "restart":
        return create_job(display_id, "restart_display", {})
    raise ValueError("Unsupported recovery action")
