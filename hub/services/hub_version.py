import os
from pathlib import Path


VERSION_FILE = Path(__file__).resolve().parents[1] / "VERSION"


def current_hub_version():
    configured = os.environ.get("HUB_VERSION", "").strip()
    if configured:
        return configured if configured.startswith("v") else f"v{configured}"
    try:
        version = VERSION_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return "development"
    return version or "development"
