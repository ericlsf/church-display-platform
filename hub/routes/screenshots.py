from flask import Blueprint, abort, jsonify

from services.config import load_config
from services.fleet_state import preview_metadata_for
from services.jobs import create_job, list_jobs


screenshots_bp = Blueprint(
    "screenshots",
    __name__,
    url_prefix="/api/v1/displays",
)


def _display_exists(display_id):
    return any(
        item.get("id") == display_id
        for item in load_config().get("displays", [])
    )


@screenshots_bp.route("/<display_id>/screenshot", methods=["GET"])
def screenshot_status(display_id):
    if not _display_exists(display_id):
        abort(404)

    metadata = preview_metadata_for(display_id)
    jobs = [
        job
        for job in list_jobs(100)
        if job.get("display_id") == display_id
        and job.get("type") == "upload_preview"
    ]
    metadata["latest_job"] = jobs[0] if jobs else None
    return jsonify(metadata)


@screenshots_bp.route("/<display_id>/screenshot", methods=["POST"])
def request_screenshot(display_id):
    if not _display_exists(display_id):
        abort(404)

    job = create_job(display_id, "upload_preview", {})
    return jsonify({"ok": True, "job": job}), 202
