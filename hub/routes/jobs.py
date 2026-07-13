from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from services.config import load_config, load_hub_settings
from services.drive import list_drive_folders
from services.events import log_event
from services.jobs import create_job, get_next_job, list_jobs, request_cancel, retry_job, update_job
from services.releases import list_git_tags


jobs_bp = Blueprint("jobs", __name__, url_prefix="/jobs")
jobs_api_bp = Blueprint("jobs_api", __name__, url_prefix="/api/v1/jobs")


@jobs_bp.route("")
def jobs_page():
    cfg = load_config()
    hub_settings = load_hub_settings()

    drive_remote = hub_settings.get("drive_remote", "gdrive")
    drive_folders, drive_error = list_drive_folders(drive_remote)
    release_tags = list_git_tags()

    return render_template(
        "jobs.html",
        active="jobs",
        displays=cfg.get("displays", []),
        jobs=list_jobs(150),
        drive_remote=drive_remote,
        drive_folders=drive_folders,
        drive_error=drive_error,
        release_tags=release_tags,
    )


@jobs_bp.route("/add", methods=["POST"])
def add_job():
    display_id = request.form.get("display_id", "").strip()
    job_type = request.form.get("job_type", "").strip()

    payload = {}

    folder = request.form.get("folder", "").strip()
    remote = request.form.get("remote", "gdrive").strip() or "gdrive"

    if folder:
        payload["folder"] = folder
        payload["remote"] = remote

    target = request.form.get("target", "").strip()
    if target:
        payload["target"] = target

    dry_run = request.form.get("dry_run", "true").strip()
    if job_type == "deploy_update":
        payload["dry_run"] = dry_run

    if not display_id or not job_type:
        return redirect(url_for("jobs.jobs_page"))

    create_job(display_id, job_type, payload)
    log_event(f"Queued job {job_type} for {display_id}")

    return redirect(url_for("jobs.jobs_page"))


@jobs_bp.route("/<job_id>/cancel", methods=["POST"])
def cancel_job(job_id):
    job = request_cancel(job_id)
    if job:
        log_event(f"Cancellation requested for job {job_id}")
    return redirect(url_for("jobs.jobs_page"))


@jobs_bp.route("/<job_id>/retry", methods=["POST"])
def retry_job_route(job_id):
    job = retry_job(job_id)
    if job:
        log_event(f"Manual retry queued for job {job_id}")
    return redirect(url_for("jobs.jobs_page"))


@jobs_api_bp.route("")
def api_list_jobs():
    return jsonify({"ok": True, "jobs": list_jobs(150)})


@jobs_api_bp.route("/next")
def api_next_job():
    display_id = (
        request.args.get("display_id")
        or request.args.get("id")
        or ""
    ).strip()

    if not display_id:
        return jsonify({"ok": False, "error": "missing display_id"}), 400

    job = get_next_job(display_id)

    if not job:
        return jsonify({"ok": True, "job": None})

    log_event(f"Job {job.get('type')} started by {display_id}")
    return jsonify({"ok": True, "job": job})


@jobs_api_bp.route("/<job_id>/status", methods=["POST"])
def api_update_job(job_id):
    payload = request.get_json(silent=True) or request.form.to_dict()

    job = update_job(
        job_id,
        status=payload.get("status"),
        progress=payload.get("progress"),
        message=payload.get("message"),
    )

    if not job:
        return jsonify({"ok": False, "error": "job not found"}), 404

    if job.get("status") in ["success", "failed", "cancelled"]:
        log_event(
            f"Job {job.get('type')} for {job.get('display_id')} finished: {job.get('status')}"
        )

    return jsonify({"ok": True, "job": job})
