from flask import Blueprint, redirect, request, url_for

from services.config import load_config
from services.events import log_event
from services.jobs import create_job


fleet_bp = Blueprint("fleet", __name__, url_prefix="/fleet")


def action_redirect():
    if request.form.get("next") == "/displays":
        return redirect(url_for("displays.displays"))
    return redirect(url_for("dashboard.dashboard"))


def queue_job(display_id, job_type, payload=None):
    job = create_job(display_id, job_type, payload or {})
    log_event(f"Queued job {job_type} for {display_id}")
    return job


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

    return action_redirect()


@fleet_bp.route("/<display_id>/sync-now", methods=["POST"])
def fleet_sync_now(display_id):
    queue_job(display_id, "sync_now")
    return action_redirect()


@fleet_bp.route("/<display_id>/restart", methods=["POST"])
def fleet_restart(display_id):
    queue_job(display_id, "restart_display")
    return action_redirect()


@fleet_bp.route("/<display_id>/reboot", methods=["POST"])
def fleet_reboot(display_id):
    queue_job(display_id, "reboot")
    return action_redirect()


@fleet_bp.route("/bulk/set-sync", methods=["POST"])
def bulk_set_sync():
    ids = request.form.getlist("display_ids")
    remote = request.form.get("sync_remote", "gdrive").strip() or "gdrive"
    folder = request.form.get("sync_folder", "Weekly").strip() or "Weekly"
    run_now = request.form.get("run_now") == "1"

    for display_id in ids:
        queue_job(display_id, "set_sync_folder", {
            "remote": remote,
            "folder": folder,
            "run_now": run_now,
        })

    return action_redirect()


@fleet_bp.route("/bulk/sync-now", methods=["POST"])
def bulk_sync_now():
    ids = request.form.getlist("display_ids")

    for display_id in ids:
        queue_job(display_id, "sync_now")

    return action_redirect()


@fleet_bp.route("/bulk/restart", methods=["POST"])
def bulk_restart():
    ids = request.form.getlist("display_ids")

    for display_id in ids:
        queue_job(display_id, "restart_display")

    return action_redirect()
