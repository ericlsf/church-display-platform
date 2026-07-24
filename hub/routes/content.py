from flask import Blueprint, flash, redirect, render_template, request, url_for

from services.config import load_hub_settings
from services.drive import list_drive_folders
from services.events import log_event
from services.jobs import create_job
from services.media import (
    analyze_drive_folder,
    discard_playlist_draft,
    get_playlist_entry,
    publish_playlist,
    save_playlist_draft,
    save_playlist_policy,
)
from services.content_cache import sync_playlist_from_drive
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


def parse_order():
    return [x.strip() for x in request.form.get("playlist_order", "").splitlines() if x.strip()]


@content_bp.route("")
def content_page():
    settings = load_hub_settings()
    remote = settings.get("drive_remote", "gdrive")
    folders, drive_error = list_drive_folders(remote)
    folder = request.args.get("folder", "").strip().strip("/")
    recursive = bool_arg("recursive")
    supported_only = request.args.get("supported_only", "1") != "0"
    analysis = current_analysis(remote, folder, recursive, supported_only)
    workflow = get_playlist_entry(remote, folder) if folder else {}

    if analysis and workflow:
        published_order = workflow.get("published_order") or analysis.get("playlist_order", [])
        by_path = {item.get("path"): item for item in analysis.get("media_items", [])}
        ordered = [by_path[path] for path in published_order if path in by_path]
        ordered.extend(item for item in analysis.get("media_items", []) if item.get("path") not in published_order)
        analysis["media_items"] = ordered

    return render_template(
        "content.html",
        active="content",
        drive_remote=remote,
        drive_folders=folders,
        drive_error=drive_error,
        selected_folder=folder,
        recursive=recursive,
        supported_only=supported_only,
        analysis=analysis,
        workflow=workflow,
    )


@content_bp.route("/save", methods=["POST"])
def save_published_order():
    folder = request.form.get("folder", "").strip().strip("/")
    remote = request.form.get("remote", "gdrive").strip() or "gdrive"
    if folder:
        order = parse_order()
        save_playlist_draft(
            remote,
            folder,
            order,
            "Saved from Images & Playlists",
        )
        published = publish_playlist(remote, folder)
        log_event(
            f"Saved playback order for {remote}:{folder} with {len(published)} item(s)",
            category="content",
        )
        flash(f"Playback order saved for {len(published)} image(s).", "success")
    return redirect(url_for("content.content_page", folder=folder, supported_only="1"))


@content_bp.route("/policy", methods=["POST"])
def save_policy():
    folder = request.form.get("folder", "").strip().strip("/")
    remote = request.form.get("remote", "gdrive").strip() or "gdrive"
    policy = save_playlist_policy(remote, folder, request.form.get("insertion_policy"))
    log_event(f"Playlist insertion policy set to {policy} for {remote}:{folder}", category="content")
    return redirect(url_for("content.content_page", folder=folder, supported_only="1"))


@content_bp.route("/order", methods=["POST"])
def save_order():
    folder = request.form.get("folder", "").strip().strip("/")
    remote = request.form.get("remote", "gdrive").strip() or "gdrive"
    if folder:
        saved = save_playlist_draft(remote, folder, parse_order(), request.form.get("draft_note", ""))
        log_event(f"Saved draft playlist for {remote}:{folder} with {len(saved)} item(s)", category="content")
        flash("Draft saved. Displays are still using the published order.", "success")
    return redirect(url_for("content.content_page", folder=folder, supported_only="1"))


@content_bp.route("/publish", methods=["POST"])
def publish_order():
    folder = request.form.get("folder", "").strip().strip("/")
    remote = request.form.get("remote", "gdrive").strip() or "gdrive"
    if folder:
        if parse_order():
            save_playlist_draft(remote, folder, parse_order(), request.form.get("draft_note", ""))
        order = publish_playlist(remote, folder)
        log_event(f"Published playlist {remote}:{folder} with {len(order)} item(s)", category="content")
        flash("Playlist published.", "success")
    return redirect(url_for("content.content_page", folder=folder, supported_only="1"))


@content_bp.route("/discard", methods=["POST"])
def discard_order():
    folder = request.form.get("folder", "").strip().strip("/")
    remote = request.form.get("remote", "gdrive").strip() or "gdrive"
    if folder:
        discard_playlist_draft(remote, folder)
        log_event(f"Discarded draft playlist for {remote}:{folder}", category="content")
        flash("Draft discarded.", "success")
    return redirect(url_for("content.content_page", folder=folder, supported_only="1"))


@content_bp.route("/deploy", methods=["POST"])
def deploy_playlist():
    display_ids = request.form.getlist("display_ids")
    folder = request.form.get("folder", "").strip().strip("/")
    remote = request.form.get("remote", "gdrive").strip() or "gdrive"
    publish_first = request.form.get("publish_first") == "1"

    if publish_first and parse_order():
        save_playlist_draft(remote, folder, parse_order(), request.form.get("draft_note", ""))
        publish_playlist(remote, folder)

    workflow = get_playlist_entry(remote, folder)
    order = workflow.get("published_order", [])

    if not folder or not display_ids:
        return redirect(url_for("content.content_page", folder=folder, supported_only="1"))
    if not order:
        flash("Publish the playlist before deploying it.", "error")
        return redirect(url_for("content.content_page", folder=folder, supported_only="1"))

    manifest, error = sync_playlist_from_drive(remote, folder)
    if error:
        log_event(f"Hub cache sync failed for {remote}:{folder}: {error}", category="content", level="error")
        flash(f"Hub cache sync failed: {error}", "error")
        return redirect(url_for("content.content_page", folder=folder, supported_only="1"))

    for display_id in display_ids:
        create_job(display_id, "set_sync_folder", {
            "remote": remote,
            "folder": folder,
            "run_now": True,
            "playlist_order": order,
        })
        log_event(f"Published playlist deploy queued for {display_id}: {remote}:{folder}", category="content")

    flash(f"Deployment queued for {len(display_ids)} display(s).", "success")
    return redirect(url_for("content.content_page", folder=folder, supported_only="1"))


@content_bp.route("/schedule", methods=["POST"])
def schedule_playlist():
    display_id = request.form.get("display_id", "").strip()
    folder = request.form.get("folder", "").strip().strip("/")
    remote = request.form.get("remote", "gdrive").strip() or "gdrive"
    run_at = request.form.get("run_at", "").strip()
    recurrence = request.form.get("recurrence", "once").strip() or "once"
    order = get_playlist_entry(remote, folder).get("published_order", [])

    if display_id and folder and run_at and order:
        create_schedule(
            name=f"Deploy {folder}",
            display_id=display_id,
            job_type="set_sync_folder",
            run_at=run_at,
            recurrence=recurrence,
            payload={"remote": remote, "folder": folder, "run_now": True, "playlist_order": order},
        )
        log_event(f"Scheduled published playlist {folder} for {display_id} at {run_at}", category="content")
        flash("Playlist deployment scheduled.", "success")
    else:
        flash("Publish the playlist before scheduling it.", "error")

    return redirect(url_for("content.content_page", folder=folder, supported_only="1"))
