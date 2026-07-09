from flask import Blueprint, redirect, render_template, request, url_for

from services.config import load_config, load_hub_settings
from services.drive import list_drive_folders
from services.events import log_event
from services.jobs import create_job
from services.media import analyze_drive_folder

media_bp = Blueprint("media", __name__, url_prefix="/media")


@media_bp.route("")
def media_page():
    cfg = load_config()
    hub_settings = load_hub_settings()
    remote = hub_settings.get("drive_remote", "gdrive")
    folders, drive_error = list_drive_folders(remote)
    selected_folder = request.args.get("folder", "").strip()
    analysis = None

    if selected_folder:
        analysis = analyze_drive_folder(remote, selected_folder)

    return render_template(
        "media.html",
        active="media",
        displays=cfg.get("displays", []),
        drive_remote=remote,
        drive_folders=folders,
        drive_error=drive_error,
        selected_folder=selected_folder,
        analysis=analysis,
    )


@media_bp.route("/sync", methods=["POST"])
def queue_media_sync():
    display_ids = request.form.getlist("display_ids")
    folder = request.form.get("folder", "").strip()
    remote = request.form.get("remote", "gdrive").strip() or "gdrive"
    run_now = request.form.get("run_now", "1") == "1"

    if not folder or not display_ids:
        return redirect(url_for("media.media_page", folder=folder))

    for display_id in display_ids:
        create_job(display_id, "set_sync_folder", {
            "remote": remote,
            "folder": folder,
            "run_now": run_now,
        })
        log_event(f"Queued media folder {folder} for {display_id}")

    return redirect(url_for("media.media_page", folder=folder))
