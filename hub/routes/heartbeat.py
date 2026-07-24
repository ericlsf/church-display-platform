from datetime import datetime
from flask import Blueprint, jsonify, request
from services.events import log_event
from services.display_address import refresh_approved_display_address
from services.heartbeat_store import load_heartbeats, save_heartbeats
from services.history import record_health_sample
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
    try:
        changed_address_fields = refresh_approved_display_address(display_id, payload)
        if changed_address_fields.intersection({"host", "ip"}):
            log_event(f"Display address updated for {display_id}: {payload.get('host')}")
    except Exception:
        # Address discovery must never prevent an otherwise valid heartbeat.
        pass
    try:
        record_health_sample(display_id, payload)
    except Exception:
        pass
    if first_seen:
        log_event(f"Heartbeat received from {display_id}")
    return jsonify({"ok": True, "agent_policy": agent_policy()})
