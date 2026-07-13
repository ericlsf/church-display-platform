from services.config import load_config, load_hub_settings
from services.jobs import create_job, list_jobs
from services.content_cache import sync_playlist_from_drive


ACTIVE = {"queued", "pending", "running", "retrying", "in_progress"}
FAILED = {"failed", "timed_out", "cancelled"}


def latest_job(display_id, job_type=None):
    for job in list_jobs(500):
        if job.get("display_id") != display_id:
            continue
        if job_type and job.get("type") != job_type:
            continue
        return job
    return None


def readiness(display, heartbeat=None):
    heartbeat = heartbeat or {}
    folder = (display.get("assigned_folder") or "").strip()

    media = heartbeat.get("media", {})
    player = heartbeat.get("player", {})

    media_count = int(
        heartbeat.get("media_count")
        or (media.get("total", 0) if isinstance(media, dict) else 0)
        or 0
    )

    player_running = bool(
        heartbeat.get("display_app_running")
        or heartbeat.get("player_running")
        or (player.get("running") if isinstance(player, dict) else False)
    )

    online = bool(heartbeat.get("online", True))
    job = latest_job(display.get("id"), "set_sync_folder")

    checks = {
        "heartbeat": online,
        "player": player_running,
        "playlist": bool(folder),
        "media": media_count > 0,
        "sync": bool(job and job.get("status") == "success"),
    }

    score = round(
        sum(1 for value in checks.values() if value)
        / len(checks)
        * 100
    )

    if all(checks.values()):
        state = "ready"
    elif not folder:
        state = "needs_playlist"
    elif job and job.get("status") in FAILED:
        state = "needs_attention"
    else:
        state = "provisioning"

    return {
        "state": state,
        "score": score,
        "checks": checks,
        "media_count": media_count,
        "job": job,
    }


def retry_initial_provisioning(display_id):
    cfg = load_config()
    display = next(
        (
            item
            for item in cfg.get("displays", [])
            if item.get("id") == display_id
        ),
        None,
    )

    if not display:
        raise ValueError("Display not found")

    folder = (display.get("assigned_folder") or "").strip()
    if not folder:
        raise ValueError("Assign a playlist before retrying provisioning")

    remote = load_hub_settings().get("drive_remote", "gdrive")
    manifest, error = sync_playlist_from_drive(remote, folder)

    if error:
        raise RuntimeError(error)

    return create_job(
        display_id,
        "set_sync_folder",
        {
            "remote": remote,
            "folder": folder,
            "run_now": True,
            "source": "hub",
            "playlist_order": manifest.get("order", []),
        },
    )
