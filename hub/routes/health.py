from flask import Blueprint, render_template
from services.events import read_events
from services.fleet_state import build_fleet_state

health_bp = Blueprint("health", __name__, url_prefix="/health")


@health_bp.route("")
def health():
    state = build_fleet_state()
    return render_template(
        "health.html",
        rows=state.get("rows", []),
        alerts=state.get("alerts", []),
        events=read_events(100),
        active="health",
    )
