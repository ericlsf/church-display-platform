from pathlib import Path

from flask import Blueprint, Response, abort, redirect, render_template, request, url_for

from services.config import load_config, load_hub_settings
from services.drive import list_drive_folders
from services.events import log_event
from services.jobs import create_job, list_jobs
from services.media import (
    analyze_drive_folder, get_playlist_revisions, media_kind, open_drive_asset_stream,
    restore_playlist_revision, save_playlist_order,
)
from services.schedules import create_schedule

content_bp = Blueprint("content", __name__, url_prefix="/content")


def bool_arg(name):
    return request.args.get(name) == "1"


def current_analysis(remote, folder, recursive=False, supported_only=True):
    if not folder:
        return None
    return analyze_drive_folder(
        remote=remote,
        folder=folder,
        recursive=recursive,
        supported_only=supported_only,
        timeout=45,
        max_items=800,
    )


@content_bp.route("")
def content_page():
    cfg = load_config()
    hub_settings = load_hub_settings()
    remote = hub_settings.get("drive_remote", "gdrive")
    folders, drive_error = list_drive_folders(remote)
    folder = request.args.get("folder", "").strip().strip("/")
    recursive = bool_arg("recursive")
    supported_only = request.args.get("supported_only", "1") != "0"
    analysis = current_analysis(remote, folder, recursive=recursive, supported_only=supported_only)

    deploy_jobs = [
        job for job in list_jobs(50)
        if job.get("type") in ["set_sync_folder", "sync_now"]
    ]

    return render_template(
        "content.html",
        active="content",
        displays=cfg.get("displays", []),
        drive_remote=remote,
        drive_folders=folders,
        drive_error=drive_error,
        selected_folder=folder,
        recursive=recursive,
        supported_only=supported_only,
        analysis=analysis,
        deploy_jobs=deploy_jobs,
        revisions=get_playlist_revisions(remote, folder) if folder else [],
    )


@content_bp.route("/order", methods=["POST"])
def save_order():
    folder = request.form.get("folder", "").strip().strip("/")
    remote = request.form.get("remote", "gdrive").strip() or "gdrive"
    order_raw = request.form.get("playlist_order", "")
    order = [x.strip() for x in order_raw.split("\n") if x.strip()]
    note = request.form.get("note", "Saved from Content Manager").strip()

    if folder:
        saved = save_playlist_order(remote, folder, order, note=note)
        log_event(f"Content playlist order saved for {remote}:{folder} with {len(saved)} item(s)")

    return redirect(url_for("content.content_page", folder=folder, supported_only="1"))


@content_bp.route("/deploy", methods=["POST"])
def deploy_playlist():
    display_ids = request.form.getlist("display_ids")
    folder = request.form.get("folder", "").strip().strip("/")
    remote = request.form.get("remote", "gdrive").strip() or "gdrive"
    order_raw = request.form.get("playlist_order", "")
    order = [x.strip() for x in order_raw.split("\n") if x.strip()]

    if folder and order:
        order = save_playlist_order(remote, folder, order)

    if not folder or not display_ids:
        return redirect(url_for("content.content_page", folder=folder, supported_only="1"))

    for display_id in display_ids:
        create_job(display_id, "set_sync_folder", {
            "remote": remote,
            "folder": folder,
            "run_now": True,
            "playlist_order": order,
        })
        log_event(f"Content playlist deploy queued for {display_id}: {remote}:{folder}")

    return redirect(url_for("content.content_page", folder=folder, supported_only="1"))


@content_bp.route("/schedule", methods=["POST"])
def schedule_playlist():
    display_id = request.form.get("display_id", "").strip()
    folder = request.form.get("folder", "").strip().strip("/")
    remote = request.form.get("remote", "gdrive").strip() or "gdrive"
    run_at = request.form.get("run_at", "").strip()
    recurrence = request.form.get("recurrence", "once").strip() or "once"
    order_raw = request.form.get("playlist_order", "")
    order = [x.strip() for x in order_raw.split("\n") if x.strip()]

    if folder and order:
        order = save_playlist_order(remote, folder, order)

    if display_id and folder and run_at:
        create_schedule(
            name=f"Deploy {folder}",
            display_id=display_id,
            job_type="set_sync_folder",
            run_at=run_at,
            recurrence=recurrence,
            payload={
                "remote": remote,
                "folder": folder,
                "run_now": True,
                "playlist_order": order,
            },
        )
        log_event(f"Scheduled content playlist {folder} for {display_id} at {run_at}")

    return redirect(url_for("content.content_page", folder=folder, supported_only="1"))


@content_bp.route("/restore", methods=["POST"])
def restore_revision():
    folder = request.form.get("folder", "").strip().strip("/")
    remote = request.form.get("remote", "gdrive").strip() or "gdrive"
    revision_index = request.form.get("revision_index", "")
    try:
        restored = restore_playlist_revision(remote, folder, revision_index)
        log_event(f"Restored content revision for {remote}:{folder} with {len(restored)} item(s)")
    except ValueError as exc:
        log_event(f"Content revision restore failed for {remote}:{folder}: {exc}")
    return redirect(url_for("content.content_page", folder=folder, supported_only="1"))


@content_bp.route("/asset")
def content_asset():
    folder = request.args.get("folder", "").strip().strip("/")
    remote = request.args.get("remote", "gdrive").strip() or "gdrive"
    path = request.args.get("path", "").strip().strip("/")
    kind = media_kind(path)
    if kind not in ["image", "video"]:
        abort(415)

    process, error = open_drive_asset_stream(remote, folder, path)
    if error:
        return Response(error, status=404, mimetype="text/plain")

    mimetype = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
        ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp",
        ".mp4": "video/mp4", ".mov": "video/quicktime", ".m4v": "video/mp4",
        ".webm": "video/webm", ".mkv": "video/x-matroska", ".avi": "video/x-msvideo",
    }.get(Path(path).suffix.lower(), "application/octet-stream")

    def generate():
        try:
            while True:
                chunk = process.stdout.read(1024 * 256)
                if not chunk:
                    break
                yield chunk
        finally:
            if process.stdout:
                process.stdout.close()
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=5)

    return Response(
        generate(), mimetype=mimetype,
        headers={"Cache-Control": "private, max-age=300", "Accept-Ranges": "none"},
    )
