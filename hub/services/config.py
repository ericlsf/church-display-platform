import json
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = APP_DIR / "config"
LOG_DIR = APP_DIR / "logs"

DISPLAYS_FILE = CONFIG_DIR / "displays.json"
HUB_SETTINGS_FILE = CONFIG_DIR / "hub.json"
PENDING_FILE = CONFIG_DIR / "pending_displays.json"
EVENT_LOG_FILE = LOG_DIR / "events.log"

CONFIG_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_CONFIG = {"displays": []}
DEFAULT_HUB_SETTINGS = {"drive_remote": "gdrive"}
DEFAULT_PENDING = {"pending": []}


def load_json(path, default):
    if not path.exists():
        save_json(path, default)
        return default
    try:
        with open(path, "r") as f:
            data = json.load(f)
    except Exception:
        data = default
    return data


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    tmp.replace(path)


def load_config():
    cfg = load_json(DISPLAYS_FILE, DEFAULT_CONFIG)
    cfg.setdefault("displays", [])
    for display in cfg["displays"]:
        display.setdefault("username", "")
        display.setdefault("password", "")
    return cfg


def save_config(cfg):
    save_json(DISPLAYS_FILE, cfg)


def load_hub_settings():
    settings = load_json(HUB_SETTINGS_FILE, DEFAULT_HUB_SETTINGS)
    settings.setdefault("drive_remote", "gdrive")
    return settings


def load_pending():
    data = load_json(PENDING_FILE, DEFAULT_PENDING)
    data.setdefault("pending", [])
    return data


def save_pending(data):
    data.setdefault("pending", [])
    save_json(PENDING_FILE, data)


def get_display(display_id):
    cfg = load_config()
    for display in cfg.get("displays", []):
        if display.get("id") == display_id:
            return display
    return None


def slugify(value):
    value = (value or "").strip().lower()
    result = []
    for ch in value:
        if ch.isalnum():
            result.append(ch)
        elif ch in [" ", "-", "_"]:
            result.append("-")
    slug = "".join(result).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "display"


def normalize_host(host):
    host = (host or "").strip()
    if not host:
        return ""
    if not host.startswith("http://") and not host.startswith("https://"):
        host = "http://" + host
    return host.rstrip("/")
