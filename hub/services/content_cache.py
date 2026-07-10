import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from services.media import get_playlist_policy, load_playlists, media_kind, playlist_key, save_playlists

HUB_DIR = Path(__file__).resolve().parent.parent
CONTENT_DIR = HUB_DIR / "content"
CACHE_DIR = CONTENT_DIR / "cache"
MANIFEST_DIR = CONTENT_DIR / "manifests"
SUPPORTED_FILTERS = [
    "+ *.jpg", "+ *.jpeg", "+ *.png", "+ *.webp", "+ *.bmp", "+ *.gif",
    "+ *.mp4", "+ *.mov", "+ *.m4v", "+ *.avi", "+ *.mkv", "+ *.webm",
    "- *",
]


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def playlist_id(remote, folder):
    raw = f"{remote or 'gdrive'}--{(folder or '').strip().strip('/')}"
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", raw).strip("-") or "playlist"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]
    return f"{slug[:80]}-{digest}"


def cache_path(remote, folder):
    return CACHE_DIR / playlist_id(remote, folder)


def manifest_path(remote, folder):
    return MANIFEST_DIR / f"{playlist_id(remote, folder)}.json"


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(cmd, timeout=600):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        return 127, "", f"Command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, "", f"Timed out after {timeout}s"
    return result.returncode, result.stdout, result.stderr


def _drive_metadata(remote, folder):
    source = f"{remote}:{folder}"
    code, out, err = _run(["rclone", "lsjson", source, "--recursive", "--files-only"], timeout=120)
    if code != 0:
        return {}, err.strip() or out.strip() or f"rclone lsjson exited {code}"
    try:
        rows = json.loads(out or "[]")
    except Exception as exc:
        return {}, f"Could not parse Drive metadata: {exc}"

    metadata = {}
    for row in rows:
        path = str(row.get("Path") or row.get("Name") or "").strip().strip("/")
        if not path or media_kind(path) not in {"image", "video"}:
            continue
        metadata[path] = {
            "modified": row.get("ModTime", ""),
            "size": int(row.get("Size", 0) or 0),
            "type": media_kind(path),
        }
    return metadata, ""


def _sync_drive(remote, folder, destination):
    destination.mkdir(parents=True, exist_ok=True)
    source = f"{remote}:{folder}"
    cmd = ["rclone", "sync", source, str(destination), "--delete-excluded"]
    for rule in SUPPORTED_FILTERS:
        cmd.extend(["--filter", rule])
    cmd.extend(["--stats-one-line", "--stats", "10s"])
    return _run(cmd, timeout=900)


def _reconcile_order(remote, folder, current_meta):
    data = load_playlists()
    key = playlist_key(remote, folder)
    entry = data.setdefault("playlists", {}).get(key, {})
    previous_order = [str(x) for x in entry.get("order", []) if str(x).strip()]
    previous_meta = entry.get("files", {}) if isinstance(entry.get("files", {}), dict) else {}
    policy = get_playlist_policy(remote, folder)

    current_names = set(current_meta)
    changed = []
    for name, meta in current_meta.items():
        old = previous_meta.get(name)
        if not old or old.get("modified") != meta.get("modified") or int(old.get("size", 0)) != int(meta.get("size", 0)):
            changed.append(name)

    def newest_key(name):
        return (current_meta.get(name, {}).get("modified", ""), name.lower())

    changed.sort(key=newest_key, reverse=True)
    changed_set = set(changed)
    unchanged_manual = [name for name in previous_order if name in current_names and name not in changed_set]
    manual_set = set(unchanged_manual)
    remaining = [name for name in current_names if name not in changed_set and name not in manual_set]

    if policy == "newest_last":
        remaining.sort(key=newest_key, reverse=True)
        order = unchanged_manual + remaining + changed
    elif policy == "alphabetical":
        order = sorted(current_names, key=str.lower)
    elif policy == "manual":
        remaining.sort(key=str.lower)
        order = unchanged_manual + remaining + changed
    else:
        remaining.sort(key=newest_key, reverse=True)
        order = changed + unchanged_manual + remaining

    data["playlists"][key] = {
        **entry,
        "remote": remote,
        "folder": folder,
        "order": order,
        "files": current_meta,
        "last_drive_sync": utc_now(),
        "insertion_policy": policy,
    }
    save_playlists(data)
    return order, changed, policy

def build_manifest(remote, folder, order, drive_meta):
    base = cache_path(remote, folder)
    file_map = {}
    for path in base.rglob("*"):
        if not path.is_file() or media_kind(path.name) not in {"image", "video"}:
            continue
        rel = path.relative_to(base).as_posix()
        meta = drive_meta.get(rel, {})
        file_map[rel] = {
            "path": rel,
            "name": path.name,
            "type": media_kind(rel),
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
            "modified": meta.get("modified", ""),
        }

    normalized_order = [name for name in order if name in file_map]
    for name in sorted(file_map):
        if name not in normalized_order:
            normalized_order.append(name)

    manifest = {
        "schema": 1,
        "playlist_id": playlist_id(remote, folder),
        "remote": remote,
        "folder": folder,
        "generated_at": utc_now(),
        "ordering_policy": get_playlist_policy(remote, folder),
        "order": normalized_order,
        "files": [file_map[name] for name in normalized_order],
    }
    target = manifest_path(remote, folder)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(manifest, indent=2))
    tmp.replace(target)
    return manifest


def sync_playlist_from_drive(remote="gdrive", folder=""):
    remote = remote or "gdrive"
    folder = (folder or "").strip().strip("/")
    if not folder:
        return None, "Folder is required"

    current_meta, error = _drive_metadata(remote, folder)
    if error:
        return None, error

    destination = cache_path(remote, folder)
    code, out, err = _sync_drive(remote, folder, destination)
    if code != 0:
        return None, err.strip() or out.strip() or f"rclone sync exited {code}"

    order, changed, policy = _reconcile_order(remote, folder, current_meta)
    manifest = build_manifest(remote, folder, order, current_meta)
    manifest["new_or_modified_front"] = changed
    manifest["insertion_policy"] = policy
    return manifest, ""


def load_manifest(remote="gdrive", folder=""):
    path = manifest_path(remote, folder)
    try:
        return json.loads(path.read_text()), ""
    except FileNotFoundError:
        return None, "Manifest not found"
    except Exception as exc:
        return None, str(exc)


def resolve_cached_file(pid, relative_path):
    base = (CACHE_DIR / pid).resolve()
    candidate = (base / relative_path).resolve()
    if base not in candidate.parents or not candidate.is_file():
        return None
    return candidate
