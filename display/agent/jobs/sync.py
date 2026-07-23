from agent.config import APP_DIR, CONFIG_PATH
from agent.utils import read_json, run_command, write_json


def save_sync_folder(remote, folder, playlist_order=None, source="hub"):
    folder = (folder or "").strip().strip("/")
    if not folder:
        raise ValueError("A playlist folder is required")

    cfg = read_json(CONFIG_PATH, {})
    cfg.setdefault("sync", {})
    cfg["sync"]["remote"] = remote or "gdrive"
    cfg["sync"]["folder"] = folder
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


def configured_folder():
    cfg = read_json(CONFIG_PATH, {})
    return (
        cfg.get("sync", {}).get("folder", "")
        if isinstance(cfg.get("sync"), dict)
        else ""
    ).strip().strip("/")


def run_sync():
    script = APP_DIR / "scripts" / "sync_media.sh"

    if not script.is_file():
        return 127, "", f"Sync script not found: {script}"

    return run_command([str(script)], cwd=str(APP_DIR), timeout=300)


def handle_sync_now(job, report):
    folder = configured_folder()

    if not folder:
        report(
            "failed",
            100,
            "No playlist folder is assigned. Use Set Folder / "
            "Approve and Provision before Sync Now.",
        )
        return

    report("running", 25, f"Starting sync for {folder}")

    code, stdout, stderr = run_sync()

    if code == 0:
        report("success", 100, f"Sync completed for {folder}")
    else:
        message = (stderr or stdout or "Sync failed").strip()[-500:]
        report("failed", 100, message)


def handle_set_sync_folder(job, report):
    payload = job.get("payload", {})
    remote = payload.get("remote", "gdrive")
    folder = (payload.get("folder") or "").strip().strip("/")
    playlist_order = payload.get("playlist_order")

    if not folder:
        report("failed", 100, "The Hub sent an empty playlist folder.")
        return

    report("running", 20, f"Saving playlist folder {folder}")

    try:
        save_sync_folder(
            remote,
            folder,
            playlist_order=playlist_order,
            source=payload.get("source", "hub"),
        )
    except Exception as exc:
        report("failed", 100, f"Could not save playlist: {exc}")
        return

    if playlist_order is not None:
        report(
            "running",
            35,
            f"Saved playlist order with {len(playlist_order)} item(s)",
        )

    report("running", 50, f"Playlist set to {folder}; starting sync")

    code, stdout, stderr = run_sync()

    if code == 0:
        report(
            "success",
            100,
            f"Playlist {folder} assigned and synchronized",
        )
    else:
        message = (
            stderr
            or stdout
            or "Playlist was saved, but synchronization failed"
        ).strip()[-500:]
        report("failed", 100, message)
