from datetime import datetime
from flask import Blueprint, render_template
from services.fleet_state import build_fleet_state


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def dashboard():
    state = build_fleet_state()
    return render_template(
        "dashboard.html",
        rows=state["rows"],
        now=datetime.now(),
        active="dashboard",
        drive_remote=state["drive_remote"],
        drive_folders=state["drive_folders"],
        drive_error=state["drive_error"],
        latest_tag=state.get("latest_tag", ""),
        outdated_count=state.get("outdated_count", 0),
        pending_count=state["pending_count"],
        events=state["events"],
        alerts=state["alerts"],
    )
