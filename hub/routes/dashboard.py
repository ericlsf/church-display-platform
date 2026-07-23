from datetime import datetime
from flask import Blueprint, render_template

from services.fleet_state import build_fleet_state
from services.jobs import list_jobs
from services.media import load_playlists
from services.notifications import build_notifications, notification_summary
from services.schedules import load_schedules
from services.resilience import load_resilience


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/legacy-dashboard")
def dashboard():
    state = build_fleet_state()
    rows = state.get("rows", [])
    jobs = list_jobs(100)
    playlists = load_playlists().get("playlists", {})
    schedules = load_schedules().get("schedules", [])
    notifications = build_notifications()[:8]

    failed_jobs = [
        job for job in jobs
        if job.get("status") in {"failed", "timed_out", "cancelled"}
        and not job.get("acknowledged")
    ]
    active_jobs = [job for job in jobs if job.get("status") in {"queued", "running"}]
    drafts = [entry for entry in playlists.values() if entry.get("status") == "draft"]

    return render_template(
        "dashboard.html",
        active="dashboard",
        now=datetime.now(),
        rows=rows,
        online_count=sum(1 for row in rows if row.get("online")),
        offline_count=sum(1 for row in rows if not row.get("online")),
        outdated_count=state.get("outdated_count", 0),
        pending_count=state.get("pending_count", 0),
        latest_tag=state.get("latest_tag", ""),
        notifications=notifications,
        notification_summary=notification_summary(),
        failed_jobs=failed_jobs[:6],
        active_jobs=active_jobs[:6],
        draft_count=len(drafts),
        published_count=sum(1 for entry in playlists.values() if entry.get("status") != "draft"),
        schedules=schedules[:6],
        events=state.get("events", [])[:8],
        maintenance=load_resilience().get("maintenance", {}),
    )
