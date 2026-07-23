import json
from pathlib import Path

from services.display_releases import build_release_package


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = ROOT / "hub" / "data" / "display-releases"
INDEX_FILE = ARTIFACT_DIR / "index.json"


def _load_index():
    if not INDEX_FILE.exists():
        return {"artifacts": {}}
    try:
        return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"artifacts": {}}


def _save_index(data):
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    temp = INDEX_FILE.with_suffix(".json.tmp")
    temp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    temp.replace(INDEX_FILE)


def artifact_path(sha256):
    return ARTIFACT_DIR / f"{sha256}.tar.gz"


def create_artifact(target):
    """
    Build a release exactly once and persist those exact bytes.

    The returned checksum is calculated from the same file later downloaded
    by the display. No package rebuild occurs at request time.
    """
    release = build_release_package(target)
    sha256 = release["sha256"]
    path = artifact_path(sha256)

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        temp = path.with_suffix(".tar.gz.tmp")
        temp.write_bytes(release["bytes"])
        temp.replace(path)

    # Verify the persisted bytes before publishing the artifact.
    import hashlib
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != sha256:
        path.unlink(missing_ok=True)
        raise RuntimeError(
            f"Persisted artifact checksum mismatch: expected {sha256}, "
            f"stored {actual}"
        )

    index = _load_index()
    index.setdefault("artifacts", {})[sha256] = {
        "target": release["target"],
        "commit": release["commit"],
        "sha256": sha256,
        "size": path.stat().st_size,
        "filename": path.name,
    }
    _save_index(index)

    return index["artifacts"][sha256]


def get_artifact(sha256):
    sha256 = (sha256 or "").strip().lower()
    if len(sha256) != 64 or any(c not in "0123456789abcdef" for c in sha256):
        return None

    path = artifact_path(sha256)
    if not path.is_file():
        return None

    index = _load_index()
    metadata = index.get("artifacts", {}).get(sha256, {})
    metadata = dict(metadata)
    metadata.setdefault("sha256", sha256)
    metadata.setdefault("size", path.stat().st_size)
    metadata["path"] = path
    return metadata
