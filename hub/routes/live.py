import json
import time
from flask import Blueprint, Response, jsonify, request
from services.config import APP_DIR
from services.events import log_event
from services.fleet_state import build_fleet_state

live_bp = Blueprint("live", __name__, url_prefix="/api/v1")


@live_bp.route("/fleet-state")
def fleet_state():
    return jsonify(build_fleet_state())


@live_bp.route("/events/fleet")
def fleet_events():
    def stream():
        while True:
            payload = json.dumps(build_fleet_state())
            yield f"event: fleet\ndata: {payload}\n\n"
            time.sleep(5)
    return Response(stream(), mimetype="text/event-stream")


@live_bp.route("/preview", methods=["POST"])
def upload_preview():
    display_id = (request.form.get("id") or "").strip()
    file = request.files.get("preview")
    if not display_id or not file:
        return jsonify({"ok": False, "error": "missing id or preview"}), 400
    preview_dir = APP_DIR / "static" / "previews"
    preview_dir.mkdir(parents=True, exist_ok=True)
    safe_id = "".join(ch for ch in display_id if ch.isalnum() or ch in "-_")
    if not safe_id:
        return jsonify({"ok": False, "error": "invalid id"}), 400
    file.save(preview_dir / f"{safe_id}.jpg")
    log_event(f"Preview updated for {safe_id}")
    return jsonify({"ok": True})
