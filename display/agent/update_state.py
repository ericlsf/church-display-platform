import json
import os
from datetime import datetime, timezone

from agent.api import post_job_status
from agent.config import APP_DIR

STATE_PATH = APP_DIR / "status" / "display_update.json"

def _now():
    return datetime.now(timezone.utc).isoformat()

def load():
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}

def save(state):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2), encoding="utf-8")
    os.replace(temporary, STATE_PATH)
    return state

def begin(job, target, previous_version):
    return save({"job_id": job.get("id"), "target": target.lstrip("v"), "previous_version": previous_version.lstrip("v"), "phase": "installing", "started_at": _now(), "updated_at": _now()})

def awaiting_checkin():
    state = load(); state.update({"phase": "awaiting_checkin", "updated_at": _now()}); return save(state)

def failed(message):
    state = load(); state.update({"phase": "failed", "message": str(message), "updated_at": _now()}); return save(state)

def finalize_after_heartbeat(installed_version):
    state = load()
    if state.get("phase") != "awaiting_checkin":
        return False
    expected = str(state.get("target", "")).lstrip("v")
    actual = str(installed_version or "").lstrip("v")
    if not expected or actual != expected:
        return False
    if state.get("job_id"):
        post_job_status(state["job_id"], "success", 100, f"Display software updated to v{actual}; agent check-in verified")
    state.update({"phase": "verified", "verified_at": _now(), "updated_at": _now()})
    save(state)
    return True