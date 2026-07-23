from flask import Blueprint, render_template

from services.fleet_dashboard import (
    build_fleet_dashboard,
)


fleet_dashboard_bp = Blueprint(
    "fleet_dashboard",
    __name__,
)


@fleet_dashboard_bp.route("/fleet-dashboard")
def page():
    return render_template(
        "fleet_dashboard.html",
        dashboard=build_fleet_dashboard(),
    )
