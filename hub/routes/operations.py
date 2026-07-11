import json
import time

from flask import Blueprint, Response, jsonify, render_template

from services.fleet_state import build_fleet_state
from services.groups import list_groups
from services.jobs import list_jobs


operations_bp = Blueprint("operations", __name__)


def operations_state():
    fleet = build_fleet_state()
    jobs = list_jobs(100)
    active_jobs = [j for j in jobs if j.get("status") in {"queued", "running"}]
    recent_jobs = jobs[:30]

    rows_by_id = {row.get("id"): row for row in fleet.get("rows", [])}
    groups = []
    for group in list_groups():
        members = [rows_by_id[i] for i in group.get("display_ids", []) if i in rows_by_id]
        groups.append({
            **group,
            "member_count": len(members),
            "online_count": sum(1 for row in members if row.get("online")),
            "outdated_count": sum(1 for row in members if row.get("update_available")),
        })

    return {
        "fleet": fleet,
        "groups": groups,
        "active_jobs": active_jobs,
        "recent_jobs": recent_jobs,
        "summary": {
            "display_count": len(fleet.get("rows", [])),
            "online_count": sum(1 for row in fleet.get("rows", []) if row.get("online")),
            "offline_count": sum(1 for row in fleet.get("rows", []) if not row.get("online")),
            "outdated_count": fleet.get("outdated_count", 0),
            "active_job_count": len(active_jobs),
            "group_count": len(groups),
        },
    }


@operations_bp.route("/operations")
def operations_page():
    return render_template("operations.html", active="operations", state=operations_state())


@operations_bp.route("/api/v1/operations-state")
def operations_state_api():
    return jsonify(operations_state())


@operations_bp.route("/api/v1/events/operations")
def operations_events():
    def stream():
        while True:
            try:
                payload = json.dumps(operations_state())
                yield f"event: operations\ndata: {payload}\n\n"
            except GeneratorExit:
                return
            except Exception as exc:
                yield f"event: error\ndata: {json.dumps({'error': str(exc)})}\n\n"
            time.sleep(3)

    response = Response(stream(), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response
