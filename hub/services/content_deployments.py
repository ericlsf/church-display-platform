import json
import os
import tempfile
from datetime import datetime, timezone
from uuid import uuid4


def _store_path():
    return os.environ.get(
        "CHURCH_DISPLAY_CONTENT_DEPLOYMENTS",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "content_deployments.json"),
    )


def _now():
    return datetime.now(timezone.utc).isoformat()


def load_store():
    path = _store_path()
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"drafts": [], "history": []}
    data.setdefault("drafts", [])
    data.setdefault("history", [])
    return data


def save_store(data):
    path = _store_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix="content-deployments-", suffix=".json", dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def create_draft(name, folder, display_ids, current_assignments, actor=""):
    store = load_store()
    draft = {
        "id": uuid4().hex,
        "name": name,
        "folder": folder,
        "display_ids": list(dict.fromkeys(display_ids)),
        "before": {did: current_assignments.get(did, "") for did in display_ids},
        "status": "draft",
        "created_at": _now(),
        "updated_at": _now(),
        "actor": actor,
    }
    store["drafts"].insert(0, draft)
    save_store(store)
    return draft


def get_draft(draft_id):
    return next((d for d in load_store()["drafts"] if d.get("id") == draft_id), None)


def delete_draft(draft_id):
    store = load_store()
    before = len(store["drafts"])
    store["drafts"] = [d for d in store["drafts"] if d.get("id") != draft_id]
    save_store(store)
    return len(store["drafts"]) != before


def publish_draft(draft_id, actor=""):
    store = load_store()
    draft = next((d for d in store["drafts"] if d.get("id") == draft_id), None)
    if not draft:
        return None
    deployment = {
        **draft,
        "id": uuid4().hex,
        "source_draft_id": draft_id,
        "status": "published",
        "published_at": _now(),
        "actor": actor or draft.get("actor", ""),
    }
    store["history"].insert(0, deployment)
    store["drafts"] = [d for d in store["drafts"] if d.get("id") != draft_id]
    save_store(store)
    return deployment


def record_rollback(deployment, actor=""):
    store = load_store()
    event = {
        "id": uuid4().hex,
        "name": f"Rollback: {deployment.get('name', 'Deployment')}",
        "folder": "",
        "display_ids": deployment.get("display_ids", []),
        "before": deployment.get("before", {}),
        "status": "rolled_back",
        "published_at": _now(),
        "actor": actor,
        "rollback_of": deployment.get("id"),
    }
    store["history"].insert(0, event)
    save_store(store)
    return event


def find_history(deployment_id):
    return next((d for d in load_store()["history"] if d.get("id") == deployment_id), None)
