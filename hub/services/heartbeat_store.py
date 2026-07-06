from services.config import CONFIG_DIR, load_json, save_json

HEARTBEATS_FILE = CONFIG_DIR / "heartbeats.json"


def load_heartbeats():
    data = load_json(HEARTBEATS_FILE, {"heartbeats": {}})
    data.setdefault("heartbeats", {})
    return data


def save_heartbeats(data):
    data.setdefault("heartbeats", {})
    save_json(HEARTBEATS_FILE, data)


def get_heartbeat_for_display(display, heartbeats):
    return (
        heartbeats.get(display.get("id", ""))
        or heartbeats.get(display.get("name", ""))
        or heartbeats.get(display.get("host", ""))
        or {}
    )
