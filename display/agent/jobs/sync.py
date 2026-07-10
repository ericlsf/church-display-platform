from agent.config import APP_DIR, CONFIG_PATH
from agent.utils import read_json, run_command, write_json


def save_sync_folder(remote, folder, playlist_order=None, source="hub"):
    cfg = read_json(CONFIG_PATH, {})
    cfg.setdefault("sync", {})
    cfg["sync"]["remote"] = remote or "gdrive"
    cfg["sync"]["folder"] = folder or "Weekly"
    cfg["sync"]["source"] = source or "hub"

    if playlist_order is not None:
        clean = []
        seen = set()
        for item in playlist_order or []:
            item = str(item).strip().strip("/")
            if item and item not in seen:
                seen.add(item)
                clean.append(item)
        cfg["sync"]["playlist_order"] = clean

    write_json(CONFIG_PATH, cfg)


def run_sync():
    script = APP_DIR / "scripts" / "sync_media.sh"
    return run_command([str(script)], cwd=str(APP_DIR), timeout=300)


def handle_sync_now(job, report):
    report("running", 25, "Starting sync")

    code, stdout, stderr = run_sync()

    if code == 0:
        report("success", 100, "Sync completed")
    else:
        message = (stderr or stdout or "Sync failed").strip()[-500:]
        report("failed", 100, message)


def handle_set_sync_folder(job, report):
    payload = job.get("payload", {})
    remote = payload.get("remote", "gdrive")
    folder = payload.get("folder", "Weekly")
    playlist_order = payload.get("playlist_order")

    report("running", 25, f"Saving folder {folder}")
    save_sync_folder(remote, folder, playlist_order=playlist_order, source=payload.get("source", "hub"))

    if playlist_order:
        report("running", 35, f"Saved playlist order with {len(playlist_order)} item(s)")

    report("running", 50, f"Folder set to {folder}; starting sync")

    code, stdout, stderr = run_sync()

    if code == 0:
        report("success", 100, "Folder set and sync completed")
    else:
        message = (stderr or stdout or "Folder set but sync failed").strip()[-500:]
        report("failed", 100, message)
