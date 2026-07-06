from datetime import datetime

from flask import Blueprint, jsonify, request

from services.config import load_json, save_json, CONFIG_DIR
from services.events import log_event


heartbeat_bp = Blueprint("heartbeat", __name__, url_prefix="/api/v1")

HEARTBEATS_FILE = CONFIG_DIR / "heartbeats.json"


def load_heartbeats():
    data = load_json(HEARTBEATS_FILE, {"heartbeats": {}})
    data.setdefault("heartbeats", {})
    return data


def save_heartbeats(data):
    data.setdefault("heartbeats", {})
    save_json(HEARTBEATS_FILE, data)


@heartbeat_bp.route("/heartbeat", methods=["POST"])
def heartbeat():
    payload = request.get_json(silent=True) or {}

    display_id = (
        payload.get("id")
        or payload.get("hostname")
        or payload.get("host")
        or ""
    ).strip()

    if not display_id:
        return jsonify({"ok": False, "error": "missing display id"}), 400

    payload["received_at"] = datetime.now().isoformat(timespec="seconds")

    data = load_heartbeats()
    first_seen = display_id not in data["heartbeats"]

    data["heartbeats"][display_id] = payload
    save_heartbeats(data)

    if first_seen:
        log_event(f"Heartbeat received from {display_id}")

    return jsonify({"ok": True})


