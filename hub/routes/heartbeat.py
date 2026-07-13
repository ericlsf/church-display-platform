from datetime import datetime
from flask import Blueprint, jsonify, request
from services.events import log_event
from services.heartbeat_store import load_heartbeats, save_heartbeats
from services.resilience import agent_policy

heartbeat_bp = Blueprint("heartbeat", __name__, url_prefix="/api/v1")


@heartbeat_bp.route("/heartbeat", methods=["POST"])
def heartbeat():
    payload = request.get_json(silent=True) or {}
    display_id = (payload.get("id") or payload.get("hostname") or payload.get("host") or "").strip()
    if not display_id:
        return jsonify({"ok": False, "error": "missing display id"}), 400
    payload["received_at"] = datetime.now().isoformat(timespec="seconds")
    data = load_heartbeats()
    first_seen = display_id not in data["heartbeats"]
    data["heartbeats"][display_id] = payload
    save_heartbeats(data)
    if first_seen:
        log_event(f"Heartbeat received from {display_id}")
    return jsonify({"ok": True, "agent_policy": agent_policy()})
