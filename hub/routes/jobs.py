from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from services.config import load_config
from services.events import log_event
from services.jobs import create_job, get_next_job, list_jobs, update_job


jobs_bp = Blueprint("jobs", __name__, url_prefix="/jobs")
jobs_api_bp = Blueprint("jobs_api", __name__, url_prefix="/api/v1/jobs")


@jobs_bp.route("")
def jobs_page():
    cfg = load_config()
    return render_template(
        "jobs.html",
        active="jobs",
        displays=cfg.get("displays", []),
        jobs=list_jobs(150),
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

    if not display_id or not job_type:
        return redirect(url_for("jobs.jobs_page"))

    create_job(display_id, job_type, payload)
    log_event(f"Queued job {job_type} for {display_id}")

    return redirect(url_for("jobs.jobs_page"))


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


