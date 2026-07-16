from flask import Blueprint, jsonify, render_template
from services.alert_center import build_alert_center

alert_center_bp = Blueprint("alert_center", __name__, url_prefix="/alerts")

@alert_center_bp.route("/")
def page():
    return render_template("alert_center.html", center=build_alert_center())

@alert_center_bp.route("/api")
def api():
    return jsonify({"ok": True, **build_alert_center()})
