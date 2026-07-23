import json
from datetime import datetime
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "management"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _safe(value):
    return "".join(ch for ch in str(value) if ch.isalnum() or ch in "-_.")[:120]


def artifact_path(display_id, kind):
    return DATA_DIR / _safe(display_id) / f"{_safe(kind)}.json"


def save_artifact(display_id, kind, payload):
    path = artifact_path(display_id, kind)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "display_id": display_id,
        "kind": kind,
        "received_at": datetime.now().isoformat(timespec="seconds"),
        "payload": payload,
    }
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(path)
    return data


def load_artifact(display_id, kind, default=None):
    path = artifact_path(display_id, kind)
    try:
        return json.loads(path.read_text())
    except Exception:
        return default if default is not None else {}


def list_artifacts(display_id):
    directory = DATA_DIR / _safe(display_id)
    if not directory.exists():
        return []
    result=[]
    for path in sorted(directory.glob("*.json")):
        try: result.append(json.loads(path.read_text()))
        except Exception: pass
    return result
