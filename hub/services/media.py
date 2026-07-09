import json
import subprocess
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}


def analyze_drive_folder(remote="gdrive", folder="", timeout=20, max_items=80):
    remote = remote or "gdrive"
    folder = (folder or "").strip().strip("/")

    if not folder:
        return {"total": 0, "images": 0, "videos": 0, "other": 0, "items": [], "error": "No folder selected"}

    source = f"{remote}:{folder}"

    try:
        result = subprocess.run(
            ["rclone", "lsjson", source, "--recursive", "--files-only"],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        return {"total": 0, "images": 0, "videos": 0, "other": 0, "items": [], "error": "rclone is not installed or not in PATH."}
    except Exception as exc:
        return {"total": 0, "images": 0, "videos": 0, "other": 0, "items": [], "error": str(exc)}

    if result.returncode != 0:
        return {
            "total": 0,
            "images": 0,
            "videos": 0,
            "other": 0,
            "items": [],
            "error": result.stderr.strip() or result.stdout.strip() or f"rclone exited with {result.returncode}",
        }

    try:
        raw_items = json.loads(result.stdout or "[]")
    except Exception as exc:
        return {"total": 0, "images": 0, "videos": 0, "other": 0, "items": [], "error": f"Could not parse rclone output: {exc}"}

    images = 0
    videos = 0
    other = 0
    items = []

    for item in raw_items:
        name = item.get("Path") or item.get("Name") or ""
        ext = Path(name).suffix.lower()
        kind = "other"

        if ext in IMAGE_EXTS:
            images += 1
            kind = "image"
        elif ext in VIDEO_EXTS:
            videos += 1
            kind = "video"
        else:
            other += 1

        if len(items) < max_items:
            items.append({
                "name": name,
                "type": kind,
                "size": item.get("Size", 0),
                "modified": item.get("ModTime", ""),
            })

    return {
        "total": len(raw_items),
        "images": images,
        "videos": videos,
        "other": other,
        "items": items,
        "error": "",
    }
