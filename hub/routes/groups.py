from flask import Blueprint, flash, redirect, render_template, request, url_for

from services.config import load_config, load_hub_settings
from services.drive import list_drive_folders
from services.events import log_event
from services.groups import create_group, delete_group, get_group, list_groups, update_group
from services.jobs import create_job
from services.releases import list_git_tags


groups_bp = Blueprint("groups", __name__, url_prefix="/groups")


def queue_for_group(group, job_type, payload=None):
    count = 0
    for display_id in group.get("display_ids", []):
        create_job(display_id, job_type, payload or {})
        count += 1
    log_event(f"Queued {job_type} for group {group.get('name')} ({count} display(s))")
    return count


@groups_bp.route("")
def groups_page():
    cfg = load_config()
    settings = load_hub_settings()
    remote = settings.get("drive_remote", "gdrive")
    folders, drive_error = list_drive_folders(remote)
    return render_template(
        "groups.html",
        active="groups",
        groups=list_groups(),
        displays=cfg.get("displays", []),
        drive_remote=remote,
        drive_folders=folders,
        drive_error=drive_error,
        release_tags=list_git_tags(),
    )


@groups_bp.route("/create", methods=["POST"])
def create_group_route():
    try:
        group = create_group(
            request.form.get("name"),
            request.form.get("description"),
            request.form.getlist("display_ids"),
        )
        log_event(f"Created display group {group['name']}")
        flash("Group created.", "success")
    except Exception as exc:
        flash(str(exc), "error")
    return redirect(url_for("groups.groups_page"))


@groups_bp.route("/<group_id>/update", methods=["POST"])
def update_group_route(group_id):
    try:
        group = update_group(
            group_id,
            request.form.get("name"),
            request.form.get("description"),
            request.form.getlist("display_ids"),
        )
        log_event(f"Updated display group {group['name']}")
        flash("Group updated.", "success")
    except Exception as exc:
        flash(str(exc), "error")
    return redirect(url_for("groups.groups_page"))


@groups_bp.route("/<group_id>/delete", methods=["POST"])
def delete_group_route(group_id):
    group = get_group(group_id)
    if group and delete_group(group_id):
        log_event(f"Deleted display group {group.get('name')}")
        flash("Group deleted.", "success")
    return redirect(url_for("groups.groups_page"))


@groups_bp.route("/<group_id>/action", methods=["POST"])
def group_action(group_id):
    group = get_group(group_id)
    if not group:
        flash("Group not found.", "error")
        return redirect(url_for("groups.groups_page"))

    action = request.form.get("action", "").strip()
    payload = {}

    if action == "sync_now":
        queue_for_group(group, "sync_now")
    elif action == "restart_display":
        queue_for_group(group, "restart_display")
    elif action == "reboot":
        queue_for_group(group, "reboot")
    elif action == "heartbeat":
        queue_for_group(group, "heartbeat")
    elif action == "set_sync_folder":
        folder = request.form.get("folder", "").strip()
        remote = request.form.get("remote", "gdrive").strip() or "gdrive"
        if not folder:
            flash("Select a folder.", "error")
            return redirect(url_for("groups.groups_page"))
        payload = {"folder": folder, "remote": remote, "run_now": True}
        queue_for_group(group, "set_sync_folder", payload)
    elif action == "deploy_update":
        target = request.form.get("target", "").strip()
        dry_run = request.form.get("dry_run", "true").strip()
        if not target:
            flash("Select a version.", "error")
            return redirect(url_for("groups.groups_page"))
        payload = {"target": target, "dry_run": dry_run}
        queue_for_group(group, "deploy_update", payload)
    else:
        flash("Unknown group action.", "error")
        return redirect(url_for("groups.groups_page"))

    flash(f"Queued {action.replace('_', ' ')} for {len(group.get('display_ids', []))} display(s).", "success")
    return redirect(url_for("groups.groups_page"))
