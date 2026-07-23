from flask import Blueprint, jsonify
from services.deployment_timeline import deployment_timeline

deployment_timeline_bp = Blueprint("deployment_timeline", __name__, url_prefix="/display")

@deployment_timeline_bp.route("/<display_id>/deployment-timeline")
def timeline(display_id):
    return jsonify({"ok": True, **deployment_timeline(display_id)})
