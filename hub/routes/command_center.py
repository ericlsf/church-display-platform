from flask import Blueprint, jsonify, redirect, url_for
from services.command_center import command_center_data

command_center_bp = Blueprint("command_center", __name__, url_prefix="/command-center")


@command_center_bp.route("")
def page():
    return redirect(url_for("fleet_dashboard.page"), code=302)


@command_center_bp.route("/summary")
def summary():
    data = command_center_data()
    return jsonify({
        "ok": True,
        "summary": data["summary"],
        "active_jobs": [
            {
                "id": job.get("id"),
                "display_id": job.get("display_id"),
                "type": job.get("type"),
                "status": job.get("status"),
                "progress": job.get("progress", 0),
            }
            for job in data["active_jobs"]
        ],
        "notifications": data["notifications"][:8],
        "generated_at": data["generated_at"],
    })
