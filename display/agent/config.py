import os
import socket
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
HUB_FALLBACK_URL = os.environ.get("HUB_FALLBACK_URL", "").rstrip("/")
HUB_URLS = tuple(
    dict.fromkeys(
        url
        for url in (HUB_URL, HUB_FALLBACK_URL)
        if url
    )
)
DISPLAY_ID = os.environ.get("DISPLAY_ID") or socket.gethostname()
DISPLAY_PORT = os.environ.get("DISPLAY_PORT", "8080")
def _installed_version():
    version_file = APP_DIR / "VERSION"
    return version_file.read_text(encoding="utf-8").strip().lstrip("v") if version_file.exists() else "unknown"


DISPLAY_VERSION = os.environ.get("DISPLAY_VERSION") or _installed_version()


