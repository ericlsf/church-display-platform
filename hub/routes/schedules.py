from flask import Blueprint, redirect, render_template, request, url_for

from services.config import load_config, load_hub_settings
from services.drive import list_drive_folders
from services.releases import list_git_tags
from services.schedules import create_schedule, delete_schedule, load_schedules, process_due_schedules, toggle_schedule

schedules_bp = Blueprint("schedules", __name__, url_prefix="/schedules")


@schedules_bp.route("")
def schedules_page():
    process_due_schedules()
    cfg = load_config()
    hub_settings = load_hub_settings()
    remote = hub_settings.get("drive_remote", "gdrive")
    folders, drive_error = list_drive_folders(remote)
    tags = list_git_tags()

    return render_template(
        "schedules.html",
        active="schedules",
        displays=cfg.get("displays", []),
        schedules=load_schedules().get("schedules", []),
        drive_remote=remote,
        drive_folders=folders,
        drive_error=drive_error,
        release_tags=tags,
    )


@schedules_bp.route("/add", methods=["POST"])
def add_schedule():
    name = request.form.get("name", "").strip()
    display_id = request.form.get("display_id", "").strip()
    job_type = request.form.get("job_type", "").strip()
    run_at = request.form.get("run_at", "").strip()
    recurrence = request.form.get("recurrence", "once").strip()
    payload = {}

    folder = request.form.get("folder", "").strip()
    remote = request.form.get("remote", "gdrive").strip() or "gdrive"
    target = request.form.get("target", "").strip()
    dry_run = request.form.get("dry_run", "true").strip()

    if folder:
        payload["folder"] = folder
        payload["remote"] = remote
    if target:
        payload["target"] = target
    if job_type == "deploy_update":
        payload["dry_run"] = dry_run

    if display_id and job_type and run_at:
        create_schedule(name, display_id, job_type, run_at, payload, recurrence)

    return redirect(url_for("schedules.schedules_page"))


@schedules_bp.route("/<schedule_id>/delete", methods=["POST"])
def delete(schedule_id):
    delete_schedule(schedule_id)
    return redirect(url_for("schedules.schedules_page"))


@schedules_bp.route("/<schedule_id>/toggle", methods=["POST"])
def toggle(schedule_id):
    toggle_schedule(schedule_id)
    return redirect(url_for("schedules.schedules_page"))


@schedules_bp.route("/process", methods=["POST"])
def process_now():
    process_due_schedules()
    return redirect(url_for("schedules.schedules_page"))
