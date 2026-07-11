from services.config import load_config, load_hub_settings
from services.groups import list_groups
from services.jobs import list_jobs
from services.media import load_playlists
from services.sites import list_sites


def _match(query, *values):
    haystack = " ".join(str(value or "") for value in values).lower()
    return query in haystack


def global_search(query, limit=100):
    query = (query or "").strip().lower()
    if not query:
        return []

    results = []

    for display in load_config().get("displays", []):
        if _match(query, display.get("id"), display.get("name"), display.get("host")):
            results.append({
                "type": "Display",
                "title": display.get("name") or display.get("id"),
                "description": f"{display.get('id', '')} · {display.get('host', '')}",
                "href": "/displays",
            })

    for group in list_groups():
        if _match(query, group.get("id"), group.get("name"), group.get("description")):
            results.append({
                "type": "Group",
                "title": group.get("name"),
                "description": f"{len(group.get('display_ids', []))} display(s)",
                "href": "/groups",
            })

    for site in list_sites():
        if _match(query, site.get("id"), site.get("name"), site.get("description")):
            results.append({
                "type": "Site",
                "title": site.get("name"),
                "description": site.get("description") or "Site",
                "href": "/sites",
            })

    playlists = load_playlists().get("playlists", {})
    for key, entry in playlists.items():
        if _match(query, key, entry.get("folder"), entry.get("remote"), entry.get("status")):
            folder = entry.get("folder") or key.split(":", 1)[-1]
            results.append({
                "type": "Playlist",
                "title": folder,
                "description": f"{entry.get('remote', 'gdrive')} · {entry.get('status', 'published')}",
                "href": f"/content?folder={folder}",
            })

    for job in list_jobs(200):
        if _match(query, job.get("id"), job.get("type"), job.get("display_id"), job.get("status"), job.get("message")):
            results.append({
                "type": "Job",
                "title": f"{job.get('type')} → {job.get('display_id')}",
                "description": f"{job.get('status')} · {job.get('message', '')}",
                "href": "/jobs",
            })

    return results[:max(1, min(int(limit), 250))]
