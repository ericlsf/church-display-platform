from services.config import load_config
from services.display_groups import load_groups
from services.fleet_operations import fleet_rows
from services.jobs import create_job


def build_fleet_map():
    rows = fleet_rows()
    by_id = {row.get("id"): row for row in rows}
    groups = load_groups().get("groups", [])

    grouped_ids = set()
    sections = []

    for group in groups:
        members = []
        for display_id in group.get("members", []):
            row = by_id.get(display_id)
            if row:
                members.append(row)
                grouped_ids.add(display_id)

        sections.append({
            "id": group.get("id", ""),
            "name": group.get("name", group.get("id", "Group")),
            "members": members,
            "summary": summarize(members),
        })

    ungrouped = [
        row for row in rows
        if row.get("id") not in grouped_ids
    ]

    if ungrouped:
        sections.append({
            "id": "ungrouped",
            "name": "Ungrouped Displays",
            "members": ungrouped,
            "summary": summarize(ungrouped),
        })

    return {
        "sections": sections,
        "summary": summarize(rows),
    }


def summarize(rows):
    return {
        "total": len(rows),
        "ready": sum(1 for row in rows if row.get("readiness") == "ready"),
        "offline": sum(1 for row in rows if row.get("readiness") == "offline"),
        "maintenance": sum(
            1 for row in rows if row.get("readiness") == "maintenance"
        ),
        "attention": sum(
            1
            for row in rows
            if row.get("readiness") in {
                "needs_attention",
                "needs_playlist",
                "provisioning",
            }
        ),
    }


def recovery_action(display_id, action):
    display = next(
        (
            item for item in load_config().get("displays", [])
            if item.get("id") == display_id
        ),
        None,
    )
    if not display:
        raise ValueError("Unknown machine")
    if display.get("device_role") == "controller" and action in {
        "restart",
        "sync",
        "retry_settings",
    }:
        raise ValueError(
            "This action only applies to display devices."
        )

    if action == "restart":
        return create_job(display_id, "restart_display", {})
    if action == "sync":
        return create_job(display_id, "sync_now", {})
    if action == "reboot":
        return create_job(display_id, "reboot", {})
    if action == "retry_settings":
        return create_job(display_id, "apply_display_settings", {})
    raise ValueError("Unsupported recovery action")
