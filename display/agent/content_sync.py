import hashlib
import json
import shutil
from urllib import parse, request

from agent.config import CONFIG_PATH, HUB_URL, MEDIA_DIR, STATUS_DIR
from agent.utils import read_json, write_json

STATUS_FILE = STATUS_DIR / "sync.json"


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_manifest(remote, folder):
    query = parse.urlencode({"remote": remote, "folder": folder})
    with request.urlopen(f"{HUB_URL}/api/v1/content/manifest?{query}", timeout=120) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not payload.get("ok"):
        raise RuntimeError(payload.get("error") or "Hub manifest request failed")
    return payload["manifest"]


def download_file(playlist_id, relative_path, destination):
    encoded = "/".join(parse.quote(part, safe="") for part in relative_path.split("/"))
    url = f"{HUB_URL}/api/v1/content/files/{parse.quote(playlist_id, safe='')}/{encoded}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_suffix(destination.suffix + ".part")
    with request.urlopen(url, timeout=300) as response, tmp.open("wb") as handle:
        shutil.copyfileobj(response, handle, length=1024 * 1024)
    tmp.replace(destination)


def sync_from_hub():
    cfg = read_json(CONFIG_PATH, {})
    sync_cfg = cfg.setdefault("sync", {})
    remote = sync_cfg.get("remote", "gdrive")
    folder = sync_cfg.get("folder", "Weekly")
    manifest = get_manifest(remote, folder)

    desired = {item["path"]: item for item in manifest.get("files", [])}
    downloaded = []
    unchanged = []

    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    for rel, item in desired.items():
        target = MEDIA_DIR / rel
        valid = target.is_file() and target.stat().st_size == int(item.get("size", -1))
        if valid and item.get("sha256"):
            valid = sha256_file(target) == item["sha256"]
        if valid:
            unchanged.append(rel)
            continue
        download_file(manifest["playlist_id"], rel, target)
        if item.get("sha256") and sha256_file(target) != item["sha256"]:
            target.unlink(missing_ok=True)
            raise RuntimeError(f"Checksum mismatch for {rel}")
        downloaded.append(rel)

    removed = []
    for path in list(MEDIA_DIR.rglob("*")):
        if path.is_file():
            rel = path.relative_to(MEDIA_DIR).as_posix()
            if rel not in desired:
                path.unlink()
                removed.append(rel)
    for path in sorted(MEDIA_DIR.rglob("*"), reverse=True):
        if path.is_dir():
            try:
                path.rmdir()
            except OSError:
                pass

    sync_cfg["source"] = "hub"
    sync_cfg["playlist_id"] = manifest.get("playlist_id")
    sync_cfg["playlist_order"] = manifest.get("order", [])
    sync_cfg["manifest_generated_at"] = manifest.get("generated_at")
    write_json(CONFIG_PATH, cfg)

    status = {
        "state": "success",
        "source": "hub",
        "folder": folder,
        "remote": remote,
        "playlist_id": manifest.get("playlist_id"),
        "files_synced": len(desired),
        "downloaded": downloaded,
        "removed": removed,
        "unchanged": unchanged,
        "change_counts": {
            "downloaded": len(downloaded),
            "removed": len(removed),
            "unchanged": len(unchanged),
        },
    }
    write_json(STATUS_FILE, status)
    return status


if __name__ == "__main__":
    print(json.dumps(sync_from_hub(), indent=2))
