import json
from datetime import datetime
from pathlib import Path

from services.config import CONFIG_DIR, load_config, slugify


GROUPS_FILE = CONFIG_DIR / "groups.json"


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def _load():
    if not GROUPS_FILE.exists():
        save_groups({"groups": []})
        return {"groups": []}
    try:
        data = json.loads(GROUPS_FILE.read_text())
    except Exception:
        data = {"groups": []}
    data.setdefault("groups", [])
    return data


def save_groups(data):
    data.setdefault("groups", [])
    GROUPS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = GROUPS_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(GROUPS_FILE)


def valid_display_ids():
    return {d.get("id") for d in load_config().get("displays", []) if d.get("id")}


def normalize_display_ids(display_ids):
    valid = valid_display_ids()
    seen = set()
    result = []
    for display_id in display_ids or []:
        display_id = str(display_id).strip()
        if display_id and display_id in valid and display_id not in seen:
            seen.add(display_id)
            result.append(display_id)
    return result


def list_groups():
    groups = _load()["groups"]
    valid = valid_display_ids()
    changed = False
    for group in groups:
        clean = [i for i in group.get("display_ids", []) if i in valid]
        if clean != group.get("display_ids", []):
            group["display_ids"] = clean
            changed = True
    if changed:
        save_groups({"groups": groups})
    return groups


def get_group(group_id):
    for group in list_groups():
        if group.get("id") == group_id:
            return group
    return None


def create_group(name, description="", display_ids=None):
    name = (name or "").strip()
    if not name:
        raise ValueError("Group name is required")

    data = _load()
    existing = {g.get("id") for g in data["groups"]}
    base_id = slugify(name)
    group_id = base_id
    counter = 2
    while group_id in existing:
        group_id = f"{base_id}-{counter}"
        counter += 1

    group = {
        "id": group_id,
        "name": name,
        "description": (description or "").strip(),
        "display_ids": normalize_display_ids(display_ids),
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    data["groups"].append(group)
    save_groups(data)
    return group


def update_group(group_id, name, description="", display_ids=None):
    data = _load()
    for group in data["groups"]:
        if group.get("id") == group_id:
            group["name"] = (name or group.get("name") or "Group").strip()
            group["description"] = (description or "").strip()
            group["display_ids"] = normalize_display_ids(display_ids)
            group["updated_at"] = now_iso()
            save_groups(data)
            return group
    raise KeyError(group_id)


def delete_group(group_id):
    data = _load()
    before = len(data["groups"])
    data["groups"] = [g for g in data["groups"] if g.get("id") != group_id]
    save_groups(data)
    return len(data["groups"]) != before
