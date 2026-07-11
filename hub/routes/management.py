from flask import Blueprint, abort, jsonify, redirect, render_template, request, url_for

from services.config import load_config
from services.events import log_event
from services.jobs import create_job, list_jobs
from services.management import load_artifact, save_artifact


management_bp = Blueprint("management", __name__, url_prefix="/management")
management_api_bp = Blueprint("management_api", __name__, url_prefix="/api/v1/management")


def _display(display_id):
    for display in load_config().get("displays", []):
        if display.get("id") == display_id:
            return display
    return None


@management_bp.route("")
def management_index():
    return render_template(
        "management_index.html",
        active="management",
        displays=load_config().get("displays", []),
    )


@management_bp.route("/<display_id>")
def management_display(display_id):
    display = _display(display_id)
    if not display:
        abort(404)

    jobs = [j for j in list_jobs(100) if j.get("display_id") == display_id][:20]
    return render_template(
        "management.html",
        active="management",
        display=display,
        logs=load_artifact(display_id, "logs", {}),
        files=load_artifact(display_id, "files", {}),
        file_content=load_artifact(display_id, "file", {}),
        jobs=jobs,
    )


@management_bp.route("/<display_id>/job", methods=["POST"])
def queue_management_job(display_id):
    if not _display(display_id):
        abort(404)
    job_type = request.form.get("job_type", "").strip()
    allowed = {"collect_logs", "list_files", "read_file", "service_action", "upload_preview"}
    if job_type not in allowed:
        abort(400)

    payload = {}
    if job_type == "read_file":
        payload["path"] = request.form.get("path", "").strip()
    if job_type == "list_files":
        payload["path"] = request.form.get("path", "").strip()
    if job_type == "service_action":
        payload["action"] = request.form.get("action", "").strip()

    create_job(display_id, job_type, payload)
    log_event(f"Queued management job {job_type} for {display_id}")
    return redirect(url_for("management.management_display", display_id=display_id))


@management_api_bp.route("/artifact/<display_id>/<kind>", methods=["POST"])
def upload_artifact(display_id, kind):
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"ok": False, "error": "JSON body required"}), 400
    save_artifact(display_id, kind, payload)
    return jsonify({"ok": True})


@management_api_bp.route("/artifact/<display_id>/<kind>")
def artifact(display_id, kind):
    return jsonify(load_artifact(display_id, kind, {}))
