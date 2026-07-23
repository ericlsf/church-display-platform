import json
from datetime import datetime
from pathlib import Path

from services.config import CONFIG_DIR

SETTINGS_FILE = CONFIG_DIR / "resilience.json"

DEFAULTS = {
    "maintenance": {
        "enabled": False,
        "message": "Maintenance in progress",
        "updated_at": "",
    },
    "recovery": {
        "enabled": True,
        "display_failure_threshold": 2,
        "restart_cooldown_seconds": 300,
        "max_restart_attempts": 3,
        "allow_reboot": False,
        "sync_repair_enabled": True,
        "sync_failure_threshold": 2,
    },
    "backups": {
        "enabled": True,
        "include_media": False,
        "retain": 6,
        "interval_days": 14,
    },
}


def _merge(defaults, data):
    result = {}
    for key, value in defaults.items():
        if isinstance(value, dict):
            result[key] = _merge(value, data.get(key, {}) if isinstance(data, dict) else {})
        else:
            result[key] = data.get(key, value) if isinstance(data, dict) else value
    return result


def load_resilience():
    try:
        data = json.loads(SETTINGS_FILE.read_text())
    except Exception:
        data = {}
    return _merge(DEFAULTS, data)


def save_resilience(data):
    merged = _merge(DEFAULTS, data)
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = SETTINGS_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(merged, indent=2))
    tmp.replace(SETTINGS_FILE)
    return merged


def set_maintenance(enabled, message=""):
    data = load_resilience()
    data["maintenance"].update({
        "enabled": bool(enabled),
        "message": (message or "Maintenance in progress").strip(),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    })
    return save_resilience(data)


def maintenance_enabled():
    return bool(load_resilience()["maintenance"].get("enabled"))


def agent_policy():
    data = load_resilience()
    return {
        "maintenance": data["maintenance"],
        "recovery": data["recovery"],
    }
