import json
from pathlib import Path

MEDIA_DIR = Path(__file__).resolve().parents[1] / "media"
CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "config.json"

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXT = {".mp4", ".mov", ".mkv"}


def load_playlist_order():
    try:
        cfg = json.loads(CONFIG_PATH.read_text())
        order = cfg.get("sync", {}).get("playlist_order", [])
    except Exception:
        order = []

    clean = []
    seen = set()
    for item in order or []:
        name = Path(str(item)).name
        if name and name not in seen:
            seen.add(name)
            clean.append(name)
    return clean


def scan_media():
    files = []

    if not MEDIA_DIR.exists():
        return files

    for f in MEDIA_DIR.iterdir():
        if f.suffix.lower() in IMAGE_EXT or f.suffix.lower() in VIDEO_EXT:
            files.append(f)

    order = load_playlist_order()
    order_index = {name: idx for idx, name in enumerate(order)}

    files.sort(key=lambda f: (order_index.get(f.name, 999999), f.name.lower()))
    return files
