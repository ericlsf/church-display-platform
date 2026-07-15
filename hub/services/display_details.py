from services.config import load_config
from services.display_groups import load_groups
from services.display_profiles import load_profiles
from services.fleet_operations import fleet_rows
from services.jobs import list_jobs
from services.audit import read_audit


def get_display_details(display_id):
    config = load_config()
    display = next(
        (
            item
            for item in config.get("displays", [])
            if item.get("id") == display_id
        ),
        None,
    )

    if not display:
        raise ValueError("Display not found")

    fleet = next(
        (
            row
            for row in fleet_rows()
            if row.get("id") == display_id
        ),
        {},
    )

    groups = [
        group
        for group in load_groups().get("groups", [])
        if display_id in group.get("members", [])
    ]

    profiles_data = load_profiles()
    profiles = profiles_data.get("profiles", [])

    jobs = [
        job
        for job in list_jobs(500)
        if job.get("display_id") == display_id
    ][:20]

    audit_rows = read_audit(
        limit=20,
        query=display_id,
    )

    presentation = display.get("presentation", {})
    maintenance = display.get(
        "maintenance",
        {"enabled": False, "reason": ""},
    )

    return {
        "display": display,
        "fleet": fleet,
        "groups": groups,
        "profiles": profiles,
        "default_profile_id": profiles_data.get(
            "default_profile_id",
            "",
        ),
        "jobs": jobs,
        "audit_rows": audit_rows,
        "presentation": presentation,
        "maintenance": maintenance,
    }
