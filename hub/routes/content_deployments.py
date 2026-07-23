from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from services.config import load_config, load_hub_settings, save_config
from services.content_deployments import (
    create_draft, delete_draft, find_history, load_store, publish_draft, record_rollback,
)
from services.events import log_event
from services.jobs import create_job
from services.media_index import cached_drive_folders

content_deployments_bp = Blueprint("content_deployments", __name__, url_prefix="/content-deployments")


def _actor():
    user = getattr(g, "current_user", None) or {}
    return user.get("username") or user.get("name") or "operator"


def _assign(cfg, display_ids, folder):
    changed = []
    for display in cfg.get("displays", []):
        if display.get("id") not in display_ids:
            continue
        display["sync_remote"] = "gdrive"
        display["sync_folder"] = folder
        display["assigned_folder"] = folder
        create_job(display.get("id"), "set_sync_folder", {"remote": "gdrive", "folder": folder})
        create_job(display.get("id"), "sync_now", {})
        changed.append(display.get("id"))
    return changed


@content_deployments_bp.route("")
def index():
    cfg = load_config()
    settings = load_hub_settings()
    folders, media_index = cached_drive_folders(settings.get("drive_remote", "gdrive"))
    store = load_store()
    display_map = {d.get("id"): d for d in cfg.get("displays", [])}
    return render_template(
        "content_deployments.html",
        active="content_deployments",
        displays=cfg.get("displays", []),
        display_map=display_map,
        folders=folders,
        media_index=media_index,
        drafts=store["drafts"],
        history=store["history"][:50],
    )


@content_deployments_bp.route("/draft", methods=["POST"])
def draft():
    cfg = load_config()
    display_ids = request.form.getlist("display_ids")
    folder = request.form.get("folder", "").strip().strip("/")
    name = request.form.get("name", "").strip() or folder or "Content deployment"
    if not display_ids or not folder:
        flash("Choose a Google Drive folder and at least one display.", "error")
        return redirect(url_for("content_deployments.index"))
    current = {
        d.get("id"): d.get("assigned_folder") or d.get("sync_folder") or ""
        for d in cfg.get("displays", [])
    }
    created = create_draft(name, folder, display_ids, current, _actor())
    log_event(f"Created content deployment draft {created['name']}")
    flash("Draft created. Review the changes before publishing.", "success")
    return redirect(url_for("content_deployments.index"))


@content_deployments_bp.route("/draft/<draft_id>/delete", methods=["POST"])
def remove_draft(draft_id):
    delete_draft(draft_id)
    flash("Draft deleted.", "success")
    return redirect(url_for("content_deployments.index"))


@content_deployments_bp.route("/draft/<draft_id>/publish", methods=["POST"])
def publish(draft_id):
    draft_data = next((d for d in load_store()["drafts"] if d.get("id") == draft_id), None)
    if not draft_data:
        flash("Draft not found.", "error")
        return redirect(url_for("content_deployments.index"))
    cfg = load_config()
    changed = _assign(cfg, draft_data.get("display_ids", []), draft_data.get("folder", ""))
    save_config(cfg)
    deployment = publish_draft(draft_id, _actor())
    log_event(f"Published content deployment {deployment['name']} to {len(changed)} display(s)")
    flash(f"Published to {len(changed)} display(s).", "success")
    return redirect(url_for("content_deployments.index"))


@content_deployments_bp.route("/history/<deployment_id>/rollback", methods=["POST"])
def rollback(deployment_id):
    deployment = find_history(deployment_id)
    if not deployment or deployment.get("status") != "published":
        flash("Deployment cannot be rolled back.", "error")
        return redirect(url_for("content_deployments.index"))
    cfg = load_config()
    restored = 0
    before = deployment.get("before", {})
    for display in cfg.get("displays", []):
        display_id = display.get("id")
        if display_id not in before:
            continue
        folder = before.get(display_id, "")
        display["sync_remote"] = "gdrive"
        display["sync_folder"] = folder
        display["assigned_folder"] = folder
        create_job(display_id, "set_sync_folder", {"remote": "gdrive", "folder": folder})
        create_job(display_id, "sync_now", {})
        restored += 1
    save_config(cfg)
    record_rollback(deployment, _actor())
    log_event(f"Rolled back content deployment {deployment.get('name')} on {restored} display(s)")
    flash(f"Rolled back {restored} display(s).", "success")
    return redirect(url_for("content_deployments.index"))
