from flask import Blueprint, flash, redirect, render_template, request, url_for

from services.fleet_map import build_fleet_map, recovery_action


fleet_map_bp = Blueprint(
    "fleet_map",
    __name__,
    url_prefix="/fleet-map",
)


@fleet_map_bp.route("")
def page():
    return redirect(url_for("displays.page"), code=302)


@fleet_map_bp.route("/recover", methods=["POST"])
def recover():
    display_id = request.form.get("display_id", "").strip()
    action = request.form.get("action", "").strip()

    try:
        recovery_action(display_id, action)
        flash(f"Queued {action} for {display_id}.", "success")
    except Exception as exc:
        flash(str(exc), "error")

    return redirect(request.referrer or url_for("fleet_map.page"))
