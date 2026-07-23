from flask import Blueprint, jsonify, render_template
from services.alert_center_state import build_alert_center_state
from services.alert_policy import apply_alert_policy

alert_center_bp = Blueprint("alert_center", __name__, url_prefix="/alerts")

@alert_center_bp.route("/")
def page():
    return render_template("alert_center.html", center=apply_alert_policy(build_alert_center_state()))

@alert_center_bp.route("/api")
def api():
    return jsonify({"ok": True, **apply_alert_policy(build_alert_center_state())})
