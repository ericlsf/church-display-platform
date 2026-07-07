import os
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = APP_DIR / "config" / "config.json"
STATUS_DIR = APP_DIR / "status"
MEDIA_DIR = APP_DIR / "media"
LOG_DIR = APP_DIR / "logs"
SCRIPTS_DIR = APP_DIR / "scripts"

STATUS_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

HUB_URL = os.environ.get("HUB_URL", "http://127.0.0.1:8090").rstrip("/")
DISPLAY_ID = os.environ.get("DISPLAY_ID") or os.uname().nodename
DISPLAY_PORT = os.environ.get("DISPLAY_PORT", "8080")
DISPLAY_VERSION = os.environ.get("DISPLAY_VERSION", "1.2.3")


