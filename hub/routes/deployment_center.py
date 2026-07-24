from flask import Blueprint, jsonify, redirect, url_for

from services.fleet_state import build_fleet_state
from services.jobs import list_jobs


deployment_center_bp = Blueprint("deployment_center", __name__)


def build_deployment_center_state():
    fleet = build_fleet_state()
    rows = fleet.get("rows", [])
    jobs = list_jobs(100)
    deployment_types = {
        "update", "upgrade", "deploy", "software_update", "content_sync",
        "sync", "publish_content", "rollback_content",
    }
    deployment_jobs = [job for job in jobs if job.get("type") in deployment_types]
    active_jobs = [job for job in deployment_jobs if job.get("status") in {"queued", "running"}]
    failed_jobs = [
        job for job in deployment_jobs
        if job.get("status") in {"failed", "timed_out"} and not job.get("acknowledged")
    ]
    attention_rows = [
        row for row in rows
        if (not row.get("online"))
        or row.get("update_available")
        or str(row.get("sync_state", "")).lower() == "error"
    ]
    return {
        "summary": {
            "display_count": len(rows),
            "online_count": sum(1 for row in rows if row.get("online")),
            "offline_count": sum(1 for row in rows if not row.get("online")),
            "update_count": sum(1 for row in rows if row.get("update_available")),
            "active_job_count": len(active_jobs),
            "failed_job_count": len(failed_jobs),
        },
        "attention_rows": attention_rows[:8],
        "active_jobs": active_jobs[:8],
        "recent_jobs": deployment_jobs[:12],
        "latest_tag": fleet.get("latest_tag") or "Unknown",
    }


@deployment_center_bp.route("/deployment-center")
def page():
    return redirect(url_for("content_deployments.page"), code=302)


@deployment_center_bp.route("/api/v1/deployment-center")
def state_api():
    return jsonify(build_deployment_center_state())
