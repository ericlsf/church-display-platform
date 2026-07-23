from flask import Blueprint, jsonify, redirect, request, url_for

from services.config import load_config
from services.display_client import get_logs
from services.events import log_event
from services.jobs import create_job
from services.releases import latest_git_tag


fleet_bp = Blueprint("fleet", __name__, url_prefix="/fleet")


def _redirect_back(default_endpoint="dashboard.dashboard"):
    target = request.form.get("next", "").strip()
    if target.startswith("/") and not target.startswith("//"):
        return redirect(target)
    return redirect(url_for(default_endpoint))


def queue_job(display_id, job_type, payload=None):
    job = create_job(display_id, job_type, payload or {})
    log_event(
        f"Queued {job_type.replace('_', ' ')} for {display_id}",
        category="fleet",
        metadata={"display_id": display_id, "job_type": job_type, "job_id": job.get("id")},
    )
    return job


def selected_display_ids():
    configured = {row.get("id") for row in load_config().get("displays", [])}
    return [display_id for display_id in request.form.getlist("display_ids") if display_id in configured]


@fleet_bp.route("/<display_id>/set-sync", methods=["POST"])
def fleet_set_sync(display_id):
    remote = request.form.get("sync_remote", "gdrive").strip() or "gdrive"
    folder = request.form.get("sync_folder", "Weekly").strip() or "Weekly"
    run_now = request.form.get("run_now") == "1"

    queue_job(display_id, "set_sync_folder", {
        "remote": remote,
        "folder": folder,
        "run_now": run_now,
    })

    return _redirect_back()


@fleet_bp.route("/<display_id>/sync-now", methods=["POST"])
def fleet_sync_now(display_id):
    queue_job(display_id, "sync_now")
    return _redirect_back()


@fleet_bp.route("/<display_id>/restart", methods=["POST"])
def fleet_restart(display_id):
    queue_job(display_id, "restart_display")
    return _redirect_back()


@fleet_bp.route("/<display_id>/reboot", methods=["POST"])
def fleet_reboot(display_id):
    queue_job(display_id, "reboot")
    return _redirect_back()


@fleet_bp.route("/<display_id>/screenshot", methods=["POST"])
def fleet_screenshot(display_id):
    queue_job(display_id, "upload_preview")
    return _redirect_back()


@fleet_bp.route("/<display_id>/update", methods=["POST"])
def fleet_update(display_id):
    target = request.form.get("target", "").strip() or latest_git_tag()
    if target:
        queue_job(display_id, "deploy_update", {"target": target, "dry_run": "false"})
    return _redirect_back()


@fleet_bp.route("/<display_id>/logs")
def fleet_logs(display_id):
    display = next(
        (row for row in load_config().get("displays", []) if row.get("id") == display_id),
        None,
    )
    if not display:
        return jsonify({"ok": False, "error": "Display not found"}), 404
    payload, online = get_logs(display)
    return jsonify({"ok": online, **payload}), 200 if online else 502


@fleet_bp.route("/bulk/set-sync", methods=["POST"])
def bulk_set_sync():
    ids = selected_display_ids()
    remote = request.form.get("sync_remote", "gdrive").strip() or "gdrive"
    folder = request.form.get("sync_folder", "Weekly").strip() or "Weekly"
    run_now = request.form.get("run_now") == "1"

    for display_id in ids:
        queue_job(display_id, "set_sync_folder", {
            "remote": remote,
            "folder": folder,
            "run_now": run_now,
        })

    return _redirect_back()


@fleet_bp.route("/bulk/sync-now", methods=["POST"])
def bulk_sync_now():
    ids = selected_display_ids()

    for display_id in ids:
        queue_job(display_id, "sync_now")

    return _redirect_back()


@fleet_bp.route("/bulk/restart", methods=["POST"])
def bulk_restart():
    ids = selected_display_ids()

    for display_id in ids:
        queue_job(display_id, "restart_display")

    return _redirect_back()


@fleet_bp.route("/bulk/screenshot", methods=["POST"])
def bulk_screenshot():
    for display_id in selected_display_ids():
        queue_job(display_id, "upload_preview")
    return _redirect_back()


@fleet_bp.route("/bulk/reboot", methods=["POST"])
def bulk_reboot():
    for display_id in selected_display_ids():
        queue_job(display_id, "reboot")
    return _redirect_back()


@fleet_bp.route("/bulk/deploy", methods=["POST"])
def bulk_deploy():
    target = request.form.get("target", "").strip() or latest_git_tag()
    if target:
        for display_id in selected_display_ids():
            queue_job(display_id, "deploy_update", {"target": target, "dry_run": "false"})
    return _redirect_back()


@fleet_bp.route("/bulk/update", methods=["POST"])
def bulk_update():
    for display_id in selected_display_ids():
        queue_job(display_id, "update_check")
    return _redirect_back()
