import json
import subprocess
from datetime import datetime
from pathlib import Path

from services.config import CONFIG_DIR

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}
SUPPORTED_EXTS = IMAGE_EXTS | VIDEO_EXTS
PLAYLISTS_FILE = CONFIG_DIR / "playlists.json"


def human_duration(seconds):
    try:
        seconds = int(seconds or 0)
    except Exception:
        seconds = 0

    if seconds <= 0:
        return "0s"

    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {sec}s"
    return f"{sec}s"


def estimated_item_seconds(kind):
    # Image timing matches the default display image duration.
    # Video runtime is not available from Google Drive metadata yet.
    if kind == "image":
        return 8
    return 0


def human_size(num):
    try:
        num = float(num or 0)
    except Exception:
        return "Unknown"

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num < 1024 or unit == "TB":
            if unit == "B":
                return f"{int(num)} {unit}"
            return f"{num:.1f} {unit}"
        num /= 1024

    return "Unknown"


def media_kind(name):
    ext = Path(name or "").suffix.lower()
    if ext in IMAGE_EXTS:
        return "image"
    if ext in VIDEO_EXTS:
        return "video"
    return "other"


def icon_for(kind, is_dir=False):
    if is_dir:
        return "📁"
    if kind == "image":
        return "🖼"
    if kind == "video":
        return "▶"
    return "📄"


def playlist_key(remote, folder):
    return f"{remote or 'gdrive'}:{(folder or '').strip().strip('/')}"


def load_playlists():
    try:
        data = json.loads(PLAYLISTS_FILE.read_text())
    except Exception:
        data = {"playlists": {}}
    data.setdefault("playlists", {})
    return data


def save_playlists(data):
    data.setdefault("playlists", {})
    PLAYLISTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = PLAYLISTS_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(PLAYLISTS_FILE)


def get_playlist_order(remote, folder):
    data = load_playlists()
    entry = data.get("playlists", {}).get(playlist_key(remote, folder), {})
    order = entry.get("order", [])
    return [str(x) for x in order if str(x).strip()]


def save_playlist_order(remote, folder, order, note="Saved from Content Manager"):
    clean = []
    seen = set()
    for item in order or []:
        item = str(item).strip().strip("/")
        if item and item not in seen:
            seen.add(item)
            clean.append(item)

    data = load_playlists()
    key = playlist_key(remote, folder)
    data.setdefault("playlists", {})
    previous = data["playlists"].get(key, {})
    previous_order = [str(x) for x in previous.get("order", []) if str(x).strip()]
    revisions = list(previous.get("revisions", []))

    if previous_order and previous_order != clean:
        revisions.insert(0, {
            "saved_at": previous.get("updated_at") or datetime.now().isoformat(timespec="seconds"),
            "note": previous.get("note") or "Previous saved order",
            "order": previous_order,
        })

    revisions = revisions[:20]
    data["playlists"][key] = {
        "remote": remote or "gdrive",
        "folder": (folder or "").strip().strip("/"),
        "order": clean,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "note": str(note or "Saved from Content Manager")[:200],
        "revisions": revisions,
    }
    save_playlists(data)
    return clean


def get_playlist_entry(remote, folder):
    data = load_playlists()
    return data.get("playlists", {}).get(playlist_key(remote, folder), {})


def get_playlist_revisions(remote, folder):
    entry = get_playlist_entry(remote, folder)
    return list(entry.get("revisions", []))


def restore_playlist_revision(remote, folder, revision_index):
    entry = get_playlist_entry(remote, folder)
    revisions = list(entry.get("revisions", []))
    try:
        revision = revisions[int(revision_index)]
    except (ValueError, TypeError, IndexError):
        raise ValueError("Revision not found")
    return save_playlist_order(
        remote, folder, revision.get("order", []),
        note=f"Restored revision from {revision.get('saved_at', 'unknown time')}",
    )


def open_drive_asset_stream(remote, folder, path):
    remote = remote or "gdrive"
    folder = (folder or "").strip().strip("/")
    path = (path or "").strip().strip("/")
    if not folder or not path or ".." in Path(path).parts:
        return None, "Invalid media path"

    source = f"{remote}:{folder}/{path}"
    try:
        probe = subprocess.run(
            ["rclone", "lsjson", source, "--stat"],
            capture_output=True, text=True, timeout=20,
        )
        if probe.returncode != 0:
            return None, probe.stderr.strip() or "Media not found"
        process = subprocess.Popen(
            ["rclone", "cat", source],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        return process, ""
    except FileNotFoundError:
        return None, "rclone is not installed or not in PATH."
    except subprocess.TimeoutExpired:
        return None, "Timed out checking media."
    except Exception as exc:
        return None, str(exc)


def rclone_lsjson(source, recursive=False, timeout=30):
    cmd = ["rclone", "lsjson", source]
    if recursive:
        cmd.append("--recursive")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        return None, "rclone is not installed or not in PATH."
    except subprocess.TimeoutExpired:
        return None, f"Timed out reading {source}."
    except Exception as exc:
        return None, str(exc)

    if result.returncode != 0:
        return None, result.stderr.strip() or result.stdout.strip() or f"rclone exited with {result.returncode}"

    try:
        return json.loads(result.stdout or "[]"), ""
    except Exception as exc:
        return None, f"Could not parse rclone output: {exc}"


def breadcrumb_parts(folder):
    folder = (folder or "").strip().strip("/")
    parts = []
    current = []

    for part in [p for p in folder.split("/") if p]:
        current.append(part)
        parts.append({"name": part, "path": "/".join(current)})

    return parts


def parent_folder(folder):
    folder = (folder or "").strip().strip("/")
    if not folder or "/" not in folder:
        return ""
    return folder.rsplit("/", 1)[0]


def ordered_media_items(items, saved_order):
    media = [item for item in items if item.get("supported") and not item.get("is_dir")]
    order_index = {name: idx for idx, name in enumerate(saved_order or [])}

    def key(item):
        path = item.get("path") or item.get("name") or ""
        name = item.get("name") or path
        idx = order_index.get(path, order_index.get(name, 999999))
        return (idx, name.lower())

    return sorted(media, key=key)


def analyze_drive_folder(remote="gdrive", folder="", timeout=30, max_items=500, recursive=False, supported_only=False):
    remote = remote or "gdrive"
    folder = (folder or "").strip().strip("/")
    saved_order = get_playlist_order(remote, folder)

    if not folder:
        return {
            "folder": "",
            "parent": "",
            "breadcrumbs": [],
            "total": 0,
            "folders": 0,
            "files": 0,
            "supported": 0,
            "images": 0,
            "videos": 0,
            "other": 0,
            "total_size": 0,
            "total_size_human": "0 B",
            "items": [],
            "media_items": [],
            "playlist_order": [],
            "error": "No folder selected",
        }

    source = f"{remote}:{folder}"
    raw_items, error = rclone_lsjson(source, recursive=recursive, timeout=timeout)

    if error:
        return {
            "folder": folder,
            "parent": parent_folder(folder),
            "breadcrumbs": breadcrumb_parts(folder),
            "total": 0,
            "folders": 0,
            "files": 0,
            "supported": 0,
            "images": 0,
            "videos": 0,
            "other": 0,
            "total_size": 0,
            "total_size_human": "0 B",
            "items": [],
            "media_items": [],
            "playlist_order": saved_order,
            "error": error,
        }

    folders = 0
    files = 0
    supported = 0
    images = 0
    videos = 0
    other = 0
    total_size = 0
    items = []

    for item in raw_items:
        name = item.get("Path") or item.get("Name") or ""
        is_dir = bool(item.get("IsDir"))
        size = item.get("Size", 0) or 0
        kind = "folder" if is_dir else media_kind(name)
        is_supported = kind in ["image", "video"]

        if is_dir:
            folders += 1
        else:
            files += 1
            total_size += int(size or 0)
            if kind == "image":
                images += 1
                supported += 1
            elif kind == "video":
                videos += 1
                supported += 1
            else:
                other += 1

        if supported_only and not is_dir and not is_supported:
            continue

        child_path = f"{folder}/{name}".strip("/") if is_dir else ""

        if len(items) < max_items:
            items.append({
                "name": name,
                "path": item.get("Path") or name,
                "child_folder": child_path,
                "type": kind,
                "icon": icon_for(kind, is_dir=is_dir),
                "is_dir": is_dir,
                "size": size,
                "size_human": human_size(size),
                "modified": item.get("ModTime", ""),
                "mime_type": item.get("MimeType", ""),
                "supported": is_supported,
                "duration_seconds": estimated_item_seconds(kind),
                "duration_human": human_duration(estimated_item_seconds(kind)) if is_supported else "",
                "resolution": "Available after sync",
            })

    items.sort(key=lambda x: (not x["is_dir"], x["type"] not in ["image", "video"], x["name"].lower()))
    media_items = ordered_media_items(items, saved_order)
    playlist_order = [item.get("path") or item.get("name") for item in media_items]
    playlist_runtime_seconds = sum(int(item.get("duration_seconds") or 0) for item in media_items)
    playlist_runtime_note = "Images estimate 8s each. Video runtime is shown after future metadata support."

    return {
        "folder": folder,
        "parent": parent_folder(folder),
        "breadcrumbs": breadcrumb_parts(folder),
        "total": len(raw_items),
        "folders": folders,
        "files": files,
        "supported": supported,
        "images": images,
        "videos": videos,
        "other": other,
        "total_size": total_size,
        "total_size_human": human_size(total_size),
        "items": items,
        "media_items": media_items,
        "playlist_order": playlist_order,
        "playlist_runtime_seconds": playlist_runtime_seconds,
        "playlist_runtime_human": human_duration(playlist_runtime_seconds),
        "playlist_runtime_note": playlist_runtime_note,
        "shown": len(items),
        "recursive": recursive,
        "supported_only": supported_only,
        "error": "",
    }
