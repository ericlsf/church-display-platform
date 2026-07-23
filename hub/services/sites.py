from services.config import CONFIG_DIR, load_json, save_json, slugify

SITES_FILE = CONFIG_DIR / "sites.json"
DEFAULT_SITES = {"sites": []}


def load_sites():
    data = load_json(SITES_FILE, DEFAULT_SITES)
    data.setdefault("sites", [])
    return data


def save_sites(data):
    data.setdefault("sites", [])
    save_json(SITES_FILE, data)


def list_sites():
    return load_sites().get("sites", [])


def get_site(site_id):
    return next((s for s in list_sites() if s.get("id") == site_id), None)


def _unique(values):
    seen, result = set(), []
    for value in values or []:
        value = (value or "").strip()
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _next_id(name, sites, current_id=None):
    base = slugify(name)
    candidate = base
    used = {s.get("id") for s in sites if s.get("id") and s.get("id") != current_id}
    counter = 2
    while candidate in used:
        candidate = f"{base}-{counter}"
        counter += 1
    return candidate


def create_site(name, description="", display_ids=None, group_ids=None):
    name = (name or "").strip()
    if not name:
        raise ValueError("Site name is required")
    data = load_sites()
    site = {
        "id": _next_id(name, data["sites"]),
        "name": name,
        "description": (description or "").strip(),
        "display_ids": _unique(display_ids),
        "group_ids": _unique(group_ids),
    }
    data["sites"].append(site)
    save_sites(data)
    return site


def update_site(site_id, name, description="", display_ids=None, group_ids=None):
    name = (name or "").strip()
    if not name:
        raise ValueError("Site name is required")
    data = load_sites()
    for site in data["sites"]:
        if site.get("id") == site_id:
            site.update({
                "id": _next_id(name, data["sites"], current_id=site_id),
                "name": name,
                "description": (description or "").strip(),
                "display_ids": _unique(display_ids),
                "group_ids": _unique(group_ids),
            })
            save_sites(data)
            return site
    raise ValueError("Site not found")


def delete_site(site_id):
    data = load_sites()
    original = len(data["sites"])
    data["sites"] = [s for s in data["sites"] if s.get("id") != site_id]
    if len(data["sites"]) == original:
        return False
    save_sites(data)
    return True


def resolve_site_display_ids(site, groups):
    display_ids = list(site.get("display_ids", []))
    groups_by_id = {group.get("id"): group for group in groups}
    for group_id in site.get("group_ids", []):
        display_ids.extend(groups_by_id.get(group_id, {}).get("display_ids", []))
    return _unique(display_ids)
