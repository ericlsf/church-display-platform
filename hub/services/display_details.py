from services.audit import read_audit
from services.config import load_config, load_hub_settings
from services.display_groups import load_groups
from services.display_profiles import load_profiles
from services.drive import list_drive_folders
from services.fleet_operations import fleet_rows
from services.jobs import list_jobs
from services.display_upgrades import display_upgrade_state
from services.health_diagnostics import build_health_diagnostics


def _system_value(system, *keys, default=None):
    for key in keys:
        value = system.get(key)
        if value not in (None, ""):
            return value
    return default


def _live_health_view(fleet, display):
    """Flatten the authoritative fleet row for the display details UI.

    Fleet telemetry is stored under ``system`` by the heartbeat pipeline. The
    older details page expected several top-level aliases, which caused its
    15-second refresh to replace good values with ``Unknown``. Keep one
    compatibility view here so both the initial render and live refresh use
    the same field meanings.
    """
    system = fleet.get("system", {}) or {}
    heartbeat = (
        fleet.get("heartbeat_age")
        or fleet.get("heartbeat")
        or fleet.get("last_seen")
        or "Unknown"
    )
    return {
        "readiness": fleet.get("readiness") or ("ready" if fleet.get("online") else "offline"),
        "cpu_temperature": _system_value(system, "cpu_temp", "temperature"),
        "memory_percent": _system_value(system, "memory_usage", "memory_percent", "ram_usage", "memory"),
        "storage_percent": _system_value(system, "disk_usage", "disk_percent", "storage_usage", "disk"),
        "ip_address": _system_value(system, "ip_address", "ip", "address", default=display.get("host", "")),
        "uptime": _system_value(system, "uptime", "system_uptime", default="Unknown"),
        "hostname": _system_value(system, "hostname", default=display.get("name") or display.get("id", "")),
        "last_heartbeat": heartbeat,
        "player_state": fleet.get("display_app_state") or ("running" if fleet.get("display_app_running") else "unknown"),
    }


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

    fleet = dict(fleet)
    fleet.update(_live_health_view(fleet, display))

    return {
        "display": display,
        "fleet": fleet,
        "health_diagnostics": build_health_diagnostics(fleet),
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
