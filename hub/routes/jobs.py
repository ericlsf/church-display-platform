from datetime import datetime, timedelta

from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from services.config import load_config, load_hub_settings
from services.drive import list_drive_folders
from services.events import log_event
from services.jobs import (
    acknowledge_all_terminal_jobs, acknowledge_job, create_job, get_next_job,
    format_job_time, job_is_resolved, job_is_unresolved_failure, list_jobs,
    parse_iso,
    request_cancel, retry_job, update_job,
)
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

    all_jobs = list_jobs(1000)
    selected_display = request.args.get("display_id", "").strip()
    selected_type = request.args.get("type", "").strip()
    selected_result = request.args.get("result", "all").strip().lower()
    try:
        days = max(1, min(int(request.args.get("days", "30")), 365))
    except ValueError:
        days = 30
    cutoff = datetime.now() - timedelta(days=days)

    def matches(job):
        timestamp = parse_iso(
            job.get("updated_at") or job.get("created_at") or ""
        )
        if timestamp and timestamp < cutoff:
            return False
        if selected_display and job.get("display_id") != selected_display:
            return False
        if selected_type and job.get("type") != selected_type:
            return False
        status = str(job.get("status", "")).lower()
        if selected_result == "unresolved" and not job_is_unresolved_failure(job):
            return False
        if selected_result == "resolved" and not job_is_resolved(job):
            return False
        if selected_result == "success" and status != "success":
            return False
        if selected_result == "active" and status not in {"queued", "running"}:
            return False
        return True

    jobs = [dict(job) for job in all_jobs if matches(job)]
    for job in jobs:
        job["created_display"] = format_job_time(job.get("created_at"))
        job["updated_display"] = format_job_time(job.get("updated_at"))

    return render_template(
        "jobs.html",
        active="jobs",
        displays=cfg.get("displays", []),
        jobs=jobs[:150],
        job_types=sorted({job.get("type", "") for job in all_jobs if job.get("type")}),
        selected_display=selected_display,
        selected_type=selected_type,
        selected_result=selected_result,
        days=days,
        unresolved_count=sum(job_is_unresolved_failure(job) for job in all_jobs),
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


@jobs_bp.route("/<job_id>/acknowledge", methods=["POST"])
def acknowledge_job_route(job_id):
    note = request.form.get("note", "").strip()
    job = acknowledge_job(job_id, note)
    if job:
        log_event(f"Marked job {job_id} resolved")
    return redirect(url_for("jobs.jobs_page"))


@jobs_bp.route("/acknowledge-terminal", methods=["POST"])
def acknowledge_terminal_jobs_route():
    count = acknowledge_all_terminal_jobs()
    log_event(f"Marked {count} terminal job(s) resolved")
    return redirect(url_for("jobs.jobs_page"))


@jobs_api_bp.route("")
def api_list_jobs():
    jobs = list_jobs(1000)
    display_id = request.args.get("display_id", "").strip()
    job_type = request.args.get("type", "").strip()
    result = request.args.get("result", "all").strip().lower()
    try:
        cutoff = datetime.now() - timedelta(
            days=max(1, min(int(request.args.get("days", "30")), 365))
        )
    except ValueError:
        cutoff = datetime.now() - timedelta(days=30)

    filtered = []
    for job in jobs:
        timestamp = parse_iso(job.get("updated_at") or job.get("created_at") or "")
        status = str(job.get("status", "")).lower()
        if timestamp and timestamp < cutoff:
            continue
        if display_id and job.get("display_id") != display_id:
            continue
        if job_type and job.get("type") != job_type:
            continue
        if result == "unresolved" and not job_is_unresolved_failure(job):
            continue
        if result == "resolved" and not job_is_resolved(job):
            continue
        if result == "success" and status != "success":
            continue
        if result == "active" and status not in {"queued", "running"}:
            continue
        filtered.append(job)
    return jsonify({"ok": True, "jobs": filtered[:150]})


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
            f"{job.get('display_id')} {job.get('type', 'job').replace('_', ' ')} {job.get('status')}",
            category="fleet",
            level="danger" if job.get("status") == "failed" else "success",
            metadata={
                "display_id": job.get("display_id"),
                "job_type": job.get("type"),
                "job_id": job.get("id"),
                "status": job.get("status"),
            },
        )

    return jsonify({"ok": True, "job": job})
