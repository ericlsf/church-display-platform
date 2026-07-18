import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from services.config import CONFIG_DIR
from services.media import (
    breadcrumb_parts,
    estimated_item_seconds,
    get_playlist_order,
    human_duration,
    human_size,
    icon_for,
    media_kind,
    ordered_media_items,
    parent_folder,
)

INDEX_FILE = CONFIG_DIR / "media_index.json"


def _utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _default_index(remote="gdrive"):
    return {
        "remote": remote or "gdrive",
        "status": "never_synced",
        "updated_at": "",
        "started_at": "",
        "error": "",
        "items": [],
    }


def load_media_index(remote="gdrive"):
    try:
        data = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = _default_index(remote)
    data.setdefault("remote", remote or "gdrive")
    data.setdefault("status", "never_synced")
    data.setdefault("updated_at", "")
    data.setdefault("started_at", "")
    data.setdefault("error", "")
    data.setdefault("items", [])
    return data


def save_media_index(data):
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = INDEX_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(INDEX_FILE)


def mark_sync_started(remote="gdrive"):
    current = load_media_index(remote)
    current.update({
        "remote": remote or "gdrive",
        "status": "syncing",
        "started_at": _utc_now(),
        "error": "",
    })
    save_media_index(current)
    return current


def refresh_media_index(remote="gdrive", timeout=180):
    remote = remote or "gdrive"
    mark_sync_started(remote)
    cmd = ["rclone", "lsjson", f"{remote}:", "--recursive"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        error = "rclone is not installed or not in PATH."
        current = load_media_index(remote)
        current.update({"status": "error", "error": error})
        save_media_index(current)
        return False, error
    except subprocess.TimeoutExpired:
        error = f"Drive index refresh timed out after {timeout} seconds. Cached media remains available."
        current = load_media_index(remote)
        current.update({"status": "error", "error": error})
        save_media_index(current)
        return False, error
    except Exception as exc:
        error = str(exc)
        current = load_media_index(remote)
        current.update({"status": "error", "error": error})
        save_media_index(current)
        return False, error

    if result.returncode != 0:
        error = result.stderr.strip() or result.stdout.strip() or f"rclone exited with {result.returncode}"
        current = load_media_index(remote)
        current.update({"status": "error", "error": error})
        save_media_index(current)
        return False, error

    try:
        raw_items = json.loads(result.stdout or "[]")
    except Exception as exc:
        error = f"Could not parse rclone output: {exc}"
        current = load_media_index(remote)
        current.update({"status": "error", "error": error})
        save_media_index(current)
        return False, error

    normalized = []
    for item in raw_items:
        path = str(item.get("Path") or item.get("Name") or "").strip("/")
        if not path:
            continue
        normalized.append({
            "Path": path,
            "Name": str(item.get("Name") or Path(path).name),
            "IsDir": bool(item.get("IsDir")),
            "Size": int(item.get("Size") or 0),
            "ModTime": str(item.get("ModTime") or ""),
            "MimeType": str(item.get("MimeType") or ""),
        })

    data = {
        "remote": remote,
        "status": "ready",
        "updated_at": _utc_now(),
        "started_at": "",
        "error": "",
        "items": normalized,
    }
    save_media_index(data)
    return True, ""


def cached_drive_folders(remote="gdrive"):
    index = load_media_index(remote)
    folders = set()
    for item in index.get("items", []):
        path = str(item.get("Path") or "").strip("/")
        if not path:
            continue
        top = path.split("/", 1)[0]
        if item.get("IsDir") or "/" in path:
            folders.add(top)
    return sorted(folders, key=str.lower), index


def _relative_item(item, folder):
    path = str(item.get("Path") or "").strip("/")
    prefix = f"{folder}/" if folder else ""
    if prefix and not path.startswith(prefix):
        return None
    rel = path[len(prefix):] if prefix else path
    if not rel:
        return None
    return rel


def analyze_cached_folder(remote="gdrive", folder="", recursive=False, supported_only=False, max_items=500):
    remote = remote or "gdrive"
    folder = (folder or "").strip().strip("/")
    saved_order = get_playlist_order(remote, folder)
    index = load_media_index(remote)

    if not folder:
        return None

    raw_items = []
    for item in index.get("items", []):
        rel = _relative_item(item, folder)
        if rel is None:
            continue
        if not recursive and "/" in rel:
            continue
        copy = dict(item)
        copy["Path"] = rel
        copy["Name"] = rel if recursive else Path(rel).name
        raw_items.append(copy)

    folders = files = supported = images = videos = other = total_size = 0
    items = []
    for item in raw_items:
        name = item.get("Path") or item.get("Name") or ""
        is_dir = bool(item.get("IsDir"))
        size = int(item.get("Size") or 0)
        kind = "folder" if is_dir else media_kind(name)
        is_supported = kind in {"image", "video"}

        if is_dir:
            folders += 1
        else:
            files += 1
            total_size += size
            if kind == "image":
                images += 1; supported += 1
            elif kind == "video":
                videos += 1; supported += 1
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
    runtime = sum(int(item.get("duration_seconds") or 0) for item in media_items)

    error = ""
    if index.get("status") == "never_synced":
        error = "Media index has not been created yet. Use Sync now; cached pages will remain available during future refreshes."
    elif not raw_items and index.get("status") == "error":
        error = index.get("error") or "Drive refresh failed and no cached items are available for this folder."

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
        "playlist_runtime_seconds": runtime,
        "playlist_runtime_human": human_duration(runtime),
        "playlist_runtime_note": "Images estimate 8s each. Video runtime is shown after future metadata support.",
        "shown": len(items),
        "recursive": recursive,
        "supported_only": supported_only,
        "error": error,
        "cache_status": index.get("status", "never_synced"),
        "cache_updated_at": index.get("updated_at", ""),
        "cache_error": index.get("error", ""),
    }
