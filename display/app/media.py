from pathlib import Path

MEDIA_DIR = Path(__file__).resolve().parents[1] / "media"

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXT = {".mp4", ".mov", ".mkv"}


def scan_media():
    files = []

    if not MEDIA_DIR.exists():
        return files

    for f in sorted(MEDIA_DIR.iterdir()):
        if f.suffix.lower() in IMAGE_EXT or f.suffix.lower() in VIDEO_EXT:
            files.append(f)

    return files
