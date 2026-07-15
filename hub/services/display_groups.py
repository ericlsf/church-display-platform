import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GROUPS_FILE = ROOT / "hub" / "config" / "display_groups.json"


def load_groups():
    if not GROUPS_FILE.exists():
        return {"groups": []}
    try:
        data = json.loads(GROUPS_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = {"groups": []}
    data.setdefault("groups", [])
    return data


def save_groups(data):
    GROUPS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = GROUPS_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(GROUPS_FILE)


def normalize_members(values):
    result = []
    seen = set()
    for value in values:
        display_id = str(value or "").strip()
        if not display_id or display_id in seen:
            continue
        seen.add(display_id)
        result.append(display_id)
    return result


def upsert_group(group_id, name, members):
    data = load_groups()
    group_id = str(group_id or "").strip()
    name = str(name or "").strip()
    members = normalize_members(members)

    if not group_id:
        raise ValueError("Group ID is required")
    if not name:
        raise ValueError("Group name is required")

    group = next(
        (item for item in data["groups"] if item.get("id") == group_id),
        None,
    )

    if group:
        group["name"] = name
        group["members"] = members
    else:
        group = {
            "id": group_id,
            "name": name,
            "members": members,
        }
        data["groups"].append(group)

    save_groups(data)
    return group


def delete_group(group_id):
    data = load_groups()
    data["groups"] = [
        item for item in data["groups"]
        if item.get("id") != group_id
    ]
    save_groups(data)


def group_members(group_ids):
    data = load_groups()
    wanted = set(group_ids or [])
    result = []
    seen = set()

    for group in data["groups"]:
        if group.get("id") not in wanted:
            continue
        for display_id in group.get("members", []):
            if display_id not in seen:
                seen.add(display_id)
                result.append(display_id)

    return result
