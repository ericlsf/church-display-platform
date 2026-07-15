from services.audit import read_audit
from services.config import load_config, load_hub_settings
from services.display_groups import load_groups
from services.display_profiles import load_profiles
from services.drive import list_drive_folders
from services.fleet_operations import fleet_rows
from services.jobs import list_jobs
from services.display_upgrades import display_upgrade_state


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

    current_folder = (
        fleet.get("assigned_folder")
        or display.get("assigned_folder")
        or display.get("sync_folder")
        or ""
    )

    remote = load_hub_settings().get(
        "drive_remote",
        "gdrive",
    )
    folders, folder_error = list_drive_folders(remote)

    # Keep the currently assigned folder selectable even if it is temporarily
    # absent from the Drive listing or the backend is unavailable.
    available_folders = []
    seen = set()

    if current_folder:
        available_folders.append(current_folder)
        seen.add(current_folder)

    for folder in folders or []:
        folder = str(folder or "").strip()
        if not folder or folder in seen:
            continue
        seen.add(folder)
        available_folders.append(folder)

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
        "current_folder": current_folder,
        "available_folders": available_folders,
        "folder_error": folder_error,
        "upgrade": display_upgrade_state(
            display_id,
            fleet.get("version", ""),
        ),
    }
