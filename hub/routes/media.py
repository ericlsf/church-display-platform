from flask import Blueprint, redirect, render_template, request, url_for

from services.config import load_config, load_hub_settings
from services.drive import list_drive_folders
from services.events import log_event
from services.jobs import create_job
from services.media import analyze_drive_folder, save_playlist_order
from services.content_cache import sync_playlist_from_drive

media_bp = Blueprint("media", __name__, url_prefix="/media")


def bool_arg(name):
    return request.args.get(name) == "1"


@media_bp.route("")
def media_page():
    cfg = load_config()
    hub_settings = load_hub_settings()
    remote = hub_settings.get("drive_remote", "gdrive")
    folders, drive_error = list_drive_folders(remote)
    selected_folder = request.args.get("folder", "").strip().strip("/")
    recursive = bool_arg("recursive")
    supported_only = bool_arg("supported_only")
    analysis = None

    if selected_folder:
        analysis = analyze_drive_folder(
            remote,
            selected_folder,
            recursive=recursive,
            supported_only=supported_only,
        )

    return render_template(
        "media.html",
        active="media",
        displays=cfg.get("displays", []),
        drive_remote=remote,
        drive_folders=folders,
        drive_error=drive_error,
        selected_folder=selected_folder,
        recursive=recursive,
        supported_only=supported_only,
        analysis=analysis,
    )


@media_bp.route("/order", methods=["POST"])
def save_media_order():
    folder = request.form.get("folder", "").strip().strip("/")
    remote = request.form.get("remote", "gdrive").strip() or "gdrive"
    order_raw = request.form.get("playlist_order", "")
    order = [x for x in order_raw.split("\n") if x.strip()]

    if folder:
        saved = save_playlist_order(remote, folder, order)
        log_event(f"Saved playlist order for {remote}:{folder} with {len(saved)} item(s)")

    return redirect(url_for("media.media_page", folder=folder, supported_only="1"))


@media_bp.route("/sync", methods=["POST"])
def queue_media_sync():
    display_ids = request.form.getlist("display_ids")
    folder = request.form.get("folder", "").strip().strip("/")
    remote = request.form.get("remote", "gdrive").strip() or "gdrive"
    run_now = request.form.get("run_now", "1") == "1"
    order_raw = request.form.get("playlist_order", "")
    playlist_order = [x for x in order_raw.split("\n") if x.strip()]

    if folder and playlist_order:
        playlist_order = save_playlist_order(remote, folder, playlist_order)

    if not folder or not display_ids:
        return redirect(url_for("media.media_page", folder=folder))

    manifest, cache_error = sync_playlist_from_drive(remote, folder)
    if cache_error:
        log_event(f"Hub cache sync failed for {remote}:{folder}: {cache_error}")
        return redirect(url_for("media.media_page", folder=folder, supported_only="1"))

    playlist_order = manifest.get("order", playlist_order)

    for display_id in display_ids:
        create_job(display_id, "set_sync_folder", {
            "remote": remote,
            "folder": folder,
            "run_now": run_now,
            "playlist_order": playlist_order,
        })
        log_event(f"Queued media folder {folder} for {display_id}")

    return redirect(url_for("media.media_page", folder=folder, supported_only="1"))
